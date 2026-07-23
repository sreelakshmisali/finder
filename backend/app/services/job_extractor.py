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
        search_result: Optional[SearchResult] = None
    ) -> Optional[NormalizedJob]:
        """
        Extracts structured job details from a career page URL.

        Args:
            url: Target career page web URL.
            search_result: Optional SearchResult context metadata.

        Returns:
            `NormalizedJob` if extraction succeeds, or `None` if page unparseable or rejected by classifier.
        """
        if not url or not isinstance(url, str):
            return None

        # 1. Fetch HTML content
        try:
            html = await self.fetcher.fetch(url)
        except Exception as exc:
            logger.warning(f"Failed to fetch content for career URL '{url}': {exc}")
            html = ""

        if not html:
            return None

        # 2. Classify Page (Gatekeeper)
        classification = self.classifier.classify(url, html)
        if not classification.is_valid_job:
            logger.info(f"Page '{url}' rejected by classifier: {classification.rejected_reason} "
                        f"(Type: {classification.page_type.value}, Conf: {classification.confidence:.2f})")
            return None

        # 3. Execute Extractor Pipeline to extract core fields
        base_job: Optional[NormalizedJob] = None
        for extractor in self.extractors:
            try:
                job = await extractor.extract(url=url, html=html, search_result=search_result)
                if job:
                    base_job = job
                    break
            except Exception as exc:
                logger.warning(f"Extractor '{extractor.name}' failed for '{url}': {exc}")

        if not base_job and not search_result:
            return None

        # Fallback if pipeline returned None but search_result exists
        if not base_job and search_result:
            base_job = await HeuristicExtractor().extract(url=url, html=html, search_result=search_result)

        if not base_job:
            return None

        # 4. Enrich with Required Skills and direct Apply URL
        skills, apply_url = SkillAndApplyExtractor.extract_skills_and_apply_url(
            page_url=url,
            html=html,
            description=base_job.description
        )

        base_job.required_skills = skills
        base_job.apply_url = apply_url or url

        return base_job
