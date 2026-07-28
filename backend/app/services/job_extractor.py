"""
Job Extractor Service

Orchestrates page fetching, page classification, pluggable metadata extraction,
skill/apply-url parsing, and normalization into `NormalizedJob` instances.
"""

import logging
from typing import Optional, List
from datetime import datetime

from app.schemas.job import NormalizedJob
from app.services.extraction.page_fetcher import SmartPageFetcher
from app.services.extraction.skill_apply_extractor import SkillAndApplyExtractor
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
                Used when the CrawlScheduler has already classified this URL
                as a JOB_POSTING with high confidence.

        Returns:
            `NormalizedJob` if extraction succeeds, or `None` if page unparseable or rejected by classifier.
        """
        if not url or not isinstance(url, str):
            print(f"[JobExtractor] SKIP: Invalid URL '{url}'")
            return None

        import time
        from app.utils.pipeline_tracker import current_tracker
        tracker = current_tracker.get()
        start = time.time()

        # 1. Fetch HTML content
        try:
            html = await self.fetcher.fetch(url)
        except Exception as exc:
            logger.warning(f"Failed to fetch content for career URL '{url}': {exc}")
            html = ""

        if not html:
            print(f"[JobExtractor] SKIP: Failed to fetch HTML for '{url}'")
            if tracker:
                tracker.record_extraction(url, success=False, extractor=None, duration=time.time() - start, error="Failed to fetch HTML")
            return None

        print(f"[JobExtractor] Fetched {len(html)} chars for: {url}")

        # 2. Classify Page (Gatekeeper)
        # Skip classification for URLs already pre-vetted by the CrawlScheduler pipeline
        if not skip_classification:
            classification = self.classifier.classify(url, html)
            if not classification.is_valid_job:
                print(
                    f"[JobExtractor] REJECTED by classifier: {classification.rejected_reason} "
                    f"(type={classification.page_type.value}, conf={classification.confidence:.2f}) "
                    f"-> {url}"
                )
                logger.info(f"Page '{url}' rejected by classifier: {classification.rejected_reason} "
                            f"(Type: {classification.page_type.value}, Conf: {classification.confidence:.2f})")
                if tracker:
                    tracker.record_extraction(url, success=False, extractor=None, duration=time.time() - start, error=f"Classifier rejected: {classification.rejected_reason}")
                return None
        else:
            print(f"[JobExtractor] Skipping gatekeeper (pre-vetted by CrawlScheduler): {url}")

        # 3. Execute Extractor Pipeline to extract core fields
        base_job: Optional[NormalizedJob] = None
        succeeded_extractor = None
        for extractor in self.extractors:
            try:
                job = await extractor.extract(url=url, html=html, search_result=search_result)
                if job:
                    base_job = job
                    succeeded_extractor = extractor.name
                    print(f"[JobExtractor] Extractor '{extractor.name}' succeeded for: {url}")
                    break
            except Exception as exc:
                logger.warning(f"Extractor '{extractor.name}' failed for '{url}': {exc}")

        if not base_job and not search_result:
            print(f"[JobExtractor] SKIP: All extractors failed and no search_result fallback for: {url}")
            if tracker:
                tracker.record_extraction(url, success=False, extractor=None, duration=time.time() - start, error="All extractors failed and no fallback")
            return None

        # Fallback if pipeline returned None but search_result exists
        if not base_job and search_result:
            print(f"[JobExtractor] Trying HeuristicExtractor fallback with search_result for: {url}")
            base_job = await HeuristicExtractor().extract(url=url, html=html, search_result=search_result)
            succeeded_extractor = "HeuristicExtractorFallback"

        if not base_job:
            print(f"[JobExtractor] SKIP: HeuristicExtractor fallback also failed for: {url}")
            if tracker:
                tracker.record_extraction(url, success=False, extractor=None, duration=time.time() - start, error="Heuristic fallback failed")
            return None

        # 4. Enrich with Required Skills and direct Apply URL
        skills, apply_url = SkillAndApplyExtractor.extract_skills_and_apply_url(
            page_url=url,
            html=html,
            description=base_job.description
        )

        base_job.required_skills = skills
        base_job.apply_url = apply_url or url

        if tracker:
            tracker.record_extraction(url, success=True, extractor=succeeded_extractor, duration=time.time() - start)

        print(f"[JobExtractor] SUCCESS: '{base_job.title}' at '{base_job.company}' -> {url}")
        return base_job

