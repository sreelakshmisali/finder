"""
Job Extractor Service

Orchestrates page fetching, page classification, pluggable metadata extraction,
skill/apply-url parsing, LinkedIn external apply link parsing (on raw HTML),
and normalization into `NormalizedJob` instances.
"""

import logging
import time
from typing import Optional, List
from datetime import datetime

from app.schemas.job import NormalizedJob
from app.services.extraction.page_fetcher import SmartPageFetcher
from app.services.extraction.skill_apply_extractor import SkillAndApplyExtractor
from app.services.crawl.linkedin_handler import LinkedInHandler
from app.services.crawl.provider_classifier import ProviderClassifier
from app.providers.search_engine.extractors.base_extractor import BaseExtractor
from app.providers.search_engine.extractors.json_ld import JsonLdExtractor
from app.providers.search_engine.extractors.open_graph import OpenGraphExtractor
from app.providers.search_engine.extractors.meta_tag import MetaTagExtractor
from app.providers.search_engine.extractors.heuristic import HeuristicExtractor
from app.providers.search_engine.base_search import SearchResult

from app.services.classification.job_page_classifier import BasePageClassifier, RuleBasedJobPageClassifier

logger = logging.getLogger(__name__)


class JobExtractor:
    """
    Main Service for converting any career page URL into a normalized Finder Job object.
    Acts as gatekeeper using JobPageClassifier.
    """

    def __init__(
        self,
        fetcher: Optional[SmartPageFetcher] = None,
        extractors: Optional[List[BaseExtractor]] = None,
        classifier: Optional[BasePageClassifier] = None
    ):
        self.fetcher = fetcher or SmartPageFetcher()
        self.extractors = extractors or [
            JsonLdExtractor(),
            OpenGraphExtractor(),
            MetaTagExtractor(),
            HeuristicExtractor()
        ]
        self.classifier = classifier or RuleBasedJobPageClassifier()

    async def extract_from_url(
        self,
        url: str,
        search_result: Optional[SearchResult] = None,
        skip_classification: bool = False,
    ) -> Optional[NormalizedJob]:
        """
        Extracts structured job details from a career page URL.

        Args:
            url: Target career page web URL.
            search_result: Optional SearchResult context metadata.
            skip_classification: If True, bypass the gatekeeper classifier.

        Returns:
            `NormalizedJob` if extraction succeeds, or `None` if page unparseable or rejected by classifier.
        """
        if not url or not isinstance(url, str):
            return None

        from app.utils.pipeline_tracker import current_tracker
        tracker = current_tracker.get()
        start = time.time()

        # 1. Fetch raw HTML content
        try:
            html = await self.fetcher.fetch(url)
        except Exception as exc:
            logger.warning(f"Failed to fetch content for career URL '{url}': {exc}")
            html = ""

        if not html:
            if tracker:
                tracker.record_extraction(url, success=False, extractor=None, duration=time.time() - start, error="FAILED_EXTRACTION: timeout")
            return None


        # 2. LinkedIn Pure HTML Parsing Pass on raw HTML (BEFORE text cleaning or gatekeeping)
        linkedin_external_apply_url: Optional[str] = None
        is_linkedin_easy_apply = False
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        netloc = parsed_url.netloc.lower()
        if "linkedin.com" in netloc:
            ext_url, is_easy = LinkedInHandler.parse_linkedin_html(html, url)
            is_linkedin_easy_apply = is_easy
            if ext_url:
                linkedin_external_apply_url = ext_url

        # 3. Classify Page (Gatekeeper)
        if not skip_classification:
            classification = self.classifier.classify(url, html)
            if not classification.is_valid_job:
                logger.warning(
                    f"[JobExtractor] REJECTED by classifier: {classification.rejected_reason} "
                    f"(type={classification.page_type.value}, conf={classification.confidence:.2f}) "
                    f"-> {url}"
                )
                if tracker:
                    tracker.record_extraction(url, success=False, extractor=None, duration=time.time() - start, error=f"FAILED_EXTRACTION: invalid HTML ({classification.rejected_reason})")
                return None
        else:
            logger.debug(f"[JobExtractor] Skipping gatekeeper (pre-vetted by CrawlScheduler): {url}")

        # 4. Execute Extractor Pipeline to extract core fields
        base_job: Optional[NormalizedJob] = None
        succeeded_extractor = None
        for extractor in self.extractors:
            try:
                job = await extractor.extract(url=url, html=html, search_result=search_result)
                if job:
                    base_job = job
                    succeeded_extractor = extractor.name
                    break
            except Exception as exc:
                logger.warning(f"Extractor '{extractor.name}' failed for '{url}': {exc}")

        if not base_job and search_result:
            base_job = await HeuristicExtractor().extract(url=url, html=html, search_result=search_result)
            succeeded_extractor = "HeuristicExtractorFallback"

        if not base_job:
            if tracker:
                tracker.record_extraction(url, success=False, extractor=None, duration=time.time() - start, error="FAILED_EXTRACTION: no job schema / parser error")
            return None

        # 5. Enrich with Required Skills and direct Apply URL
        skills, apply_url = SkillAndApplyExtractor.extract_skills_and_apply_url(
            page_url=url,
            html=html,
            description=base_job.description
        )

        base_job.required_skills = skills
        
        # Override apply_url / url / source if it's a LinkedIn page
        if "linkedin.com" in netloc:
            base_job.url = url
            base_job.source = "linkedin"
            if linkedin_external_apply_url:
                base_job.apply_url = linkedin_external_apply_url
                base_job.can_apply = True
            else:
                # No external ATS link discovered from LinkedIn HTML (could be Easy Apply or require login)
                base_job.apply_url = None
                base_job.can_apply = False
        else:
            # Standard ATS or Career Page
            base_job.apply_url = apply_url
            if base_job.apply_url:
                base_job.can_apply = True
            else:
                base_job.can_apply = False

        # Classify the URL using ProviderClassifier to check for direct ATS providers
        from app.services.crawl.provider_classifier import ProviderClassifier
        provider_tag = ProviderClassifier.classify(url)
        
        DIRECT_ATS_PROVIDERS = {
            "greenhouse", "lever", "ashby", "workday", 
            "smartrecruiters", "jobvite", "bamboohr", "workable",
            "infopark", "technopark"
        }
        is_direct_ats = provider_tag in DIRECT_ATS_PROVIDERS

        # --- Validation Logic for apply_url ---
        # 1. Reject if apply_url is None and it is NOT a direct/trusted ATS provider
        if not base_job.apply_url:
            if is_direct_ats:
                base_job.apply_url = url
                base_job.can_apply = True
            else:
                logger.info(f"Rejecting job because apply_url is None and not a direct ATS provider: {url}")
                if tracker:
                    tracker.record_extraction(url, success=False, extractor=None, duration=time.time() - start, error="FAILED_EXTRACTION: apply_url is None and not direct ATS")
                return None

        # 2. Check if apply_url is a valid URL format
        from urllib.parse import urlparse as parse_url
        parsed_apply = parse_url(base_job.apply_url)
        if not parsed_apply.scheme or not parsed_apply.netloc:
            logger.info(f"Rejecting job because apply_url is invalid: '{base_job.apply_url}' for source: {url}")
            if tracker:
                tracker.record_extraction(url, success=False, extractor=None, duration=time.time() - start, error=f"FAILED_EXTRACTION: invalid apply_url format '{base_job.apply_url}'")
            return None

        # 3. Must not equal source page URL (url) unless allowed provider
        if base_job.apply_url == url and not is_direct_ats:
            logger.info(f"Rejecting job because apply_url equals source page URL: {url}")
            if tracker:
                tracker.record_extraction(url, success=False, extractor=None, duration=time.time() - start, error="FAILED_EXTRACTION: apply_url equals source page URL")
            return None

        # 4. Enforce linkedin_mode configuration and prevent LinkedIn apply URLs in external_only mode
        from app.core.scheduler_config import SchedulerConfig
        config = SchedulerConfig.from_env()

        if "linkedin.com" in netloc and config.linkedin_mode == "external_only" and not base_job.can_apply:
            logger.info(f"Rejecting LinkedIn Easy Apply / non-external job: {url}")
            if tracker:
                tracker.record_extraction(url, success=False, extractor=None, duration=time.time() - start, error="FAILED_EXTRACTION: LinkedIn Easy Apply/Non-external posting rejected")
            return None

        if "linkedin.com" in parsed_apply.netloc.lower() and config.linkedin_mode == "external_only":
            logger.info(f"Rejecting job because apply_url is a LinkedIn URL in external_only mode: {base_job.apply_url} for source: {url}")
            if tracker:
                tracker.record_extraction(url, success=False, extractor=None, duration=time.time() - start, error="FAILED_EXTRACTION: apply_url is LinkedIn in external_only mode")
            return None

        if tracker:
            tracker.record_extraction(url, success=True, extractor=succeeded_extractor, duration=time.time() - start)

        return base_job
