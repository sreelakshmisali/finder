"""
Search Engine Job Discovery Provider

Unified `JobDiscoveryProvider` implementing a true multi-stage crawler pipeline:

Stage 1 — Query Enrichment:
    Raw user query → multiple targeted job-search queries
    e.g. "react" → ["react developer jobs", "site:boards.greenhouse.io react", ...]

Stage 2 — Multi-Engine Search Aggregation:
    All enriched queries run concurrently across search providers (DuckDuckGo default).
    Results are merged and deduplicated into a list of candidate URLs.

Stage 3 — CrawlScheduler (classification, drill-down, SWRR budget allocation):
    Candidate URLs → classification → ATS/listing drill-down → SWRR diversity scheduler
    returns fair, TaggedURLs with inherited parent SearchResult context.

Stage 4 — Job Extraction:
    Only diversity-allocated posting TaggedURLs reach JobExtractor.
    JobExtractor fetches, parses, applies LinkedIn pure HTML parser, and returns NormalizedJob objects.
"""

import asyncio
import logging
from typing import List, Optional, Any

from app.providers.base_discovery import SearchEngineProvider, DiscoveryContext
from app.providers.search_engine.base_search import SearchProvider
from app.services.search_aggregator import SearchAggregator
from app.services.search_query_generator import SearchQueryGenerator
from app.services.crawl.crawl_scheduler import CrawlScheduler
from app.services.crawl.url_utils import URLDeduplicator
from app.schemas.job import NormalizedJob
from app.schemas.tagged_url import TaggedURL

logger = logging.getLogger(__name__)


class SearchDiscoveryProvider(SearchEngineProvider):
    """
    Unified Discovery Provider for Multi-Search Engine job discovery.

    Implements a multi-stage pipeline:
      Search Engines → Candidate URLs → CrawlScheduler (SWRR) → Job Posting TaggedURLs → JobExtractor
    """

    def __init__(
        self,
        search_providers: Optional[List[SearchProvider]] = None,
        aggregator: Optional[SearchAggregator] = None,
        job_extractor: Optional[Any] = None,
        scheduler: Optional[CrawlScheduler] = None,
    ):
        if aggregator:
            self.aggregator = aggregator
        elif search_providers:
            self.aggregator = SearchAggregator(search_providers=search_providers)
        else:
            self.aggregator = SearchAggregator()

        self._job_extractor = job_extractor
        self._scheduler = scheduler

    @property
    def job_extractor(self):
        if self._job_extractor is None:
            from app.services.job_extractor import JobExtractor
            self._job_extractor = JobExtractor()
        return self._job_extractor

    @property
    def scheduler(self) -> CrawlScheduler:
        if self._scheduler is None:
            self._scheduler = CrawlScheduler()
        return self._scheduler

    @property
    def source_name(self) -> str:
        return "search_engine"

    @property
    def display_name(self) -> str:
        return "Search Engine Discovery"

    @property
    def description(self) -> str:
        return (
            "Discovers tech job postings via a multi-stage crawler: "
            "DuckDuckGo Search → PageType classification → "
            "ATS/listing page drill-down → SWRR diversity scheduler → individual job extraction."
        )

    async def discover(self, context: DiscoveryContext) -> List[NormalizedJob]:
        """
        Executes multi-stage search discovery pipeline:
        Stage 1: Query Enrichment
        Stage 2: Search Engine Aggregation
        Stage 3: CrawlScheduler (classification & drill-down to job URLs)
        Stage 4: Job Extraction from vetted job URLs
        Stage 5: Deduplication & Company Limiting
        """
        from app.utils.pipeline_tracker import current_tracker
        tracker = context.metadata.get("tracker")
        tracker_token = None
        if tracker:
            tracker_token = current_tracker.set(tracker)
            tracker.start_stage("Stage 1 - Search Engine Discovery")

        raw_query = context.query.query or ""
        location = context.query.location or ""
        limit = context.query.limit

        # Stage 1 — Query Enrichment
        enriched_queries = SearchQueryGenerator.generate_search_engine_queries(
            raw_query=raw_query,
            location=location,
            max_queries=10,
        )
        if not enriched_queries:
            search_term = f"{raw_query} {location}".strip()
            enriched_queries = [search_term] if search_term else []

        if not enriched_queries:
            return []

        # Stage 2 — Multi-engine search aggregation
        candidate_results = await self.aggregator.aggregate_multi_query(
            queries=enriched_queries,
            raw_query=raw_query,
            limit_per_query=10,
            total_limit=limit * 3,
        )
        candidate_urls = [r.url for r in candidate_results]

        if not candidate_urls:
            logger.warning("[SearchDiscovery] No candidate URLs returned from search engines.")
            return []

        # Stage 3 — CrawlScheduler: Classify, drill down into listing/career pages, allocate fair budget
        global_dedup = URLDeduplicator()
        job_posting_urls = await self.scheduler.schedule(
            candidate_urls=candidate_urls,
            global_dedup=global_dedup,
            target_role=raw_query,
            candidate_results=candidate_results,
        )

        # Fallback: if CrawlScheduler returned empty, try direct candidate URLs that look like job postings
        if not job_posting_urls:
            logger.info("[SearchDiscovery] CrawlScheduler yielded 0 URLs. Attempting candidate fallback.")
            target_urls = candidate_urls[:limit]
            url_to_result = {r.url: r for r in candidate_results}
            extraction_tasks = [
                self.job_extractor.extract_from_url(
                    url=url,
                    search_result=url_to_result.get(url),
                    skip_classification=False,
                )
                for url in target_urls
            ]
        else:
            url_to_result = {r.url: r for r in candidate_results}
            extraction_tasks = [
                self.job_extractor.extract_from_url(
                    url=tagged.url if hasattr(tagged, "url") else str(tagged),
                    search_result=url_to_result.get(tagged.url if hasattr(tagged, "url") else str(tagged)),
                    skip_classification=False,
                )
                for tagged in job_posting_urls[:limit]
            ]

        # Stage 4 — Job Extraction
        extracted = await asyncio.gather(*extraction_tasks, return_exceptions=True)

        # Filter successfully extracted NormalizedJobs
        normalized_jobs: List[NormalizedJob] = []
        for result in extracted:
            if isinstance(result, NormalizedJob):
                normalized_jobs.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"[SearchDiscovery] Job extraction failed: {result}")

        # Stage 5 — Deduplication & Company Limiting
        max_jobs_per_company = self.scheduler.config.max_jobs_per_company or 5
        company_groups = {}
        for job in normalized_jobs:
            c_name = job.company.strip().lower() if job.company else "unknown"
            if c_name not in company_groups:
                company_groups[c_name] = []
            company_groups[c_name].append(job)

        final_jobs: List[NormalizedJob] = []
        seen_fingerprints = set()

        for c_name, c_jobs in company_groups.items():
            limited = c_jobs[:max_jobs_per_company]
            for job in limited:
                title_clean = job.title.strip().lower()
                loc_clean = job.location.strip().lower()
                fingerprint = f"{c_name}|{title_clean}|{loc_clean}"
                if fingerprint not in seen_fingerprints:
                    seen_fingerprints.add(fingerprint)
                    final_jobs.append(job)

        if tracker:
            tracker.complete()
            if tracker_token:
                current_tracker.reset(tracker_token)

        return final_jobs


    async def get_details(self, url: str) -> Optional[NormalizedJob]:
        """Fetch details for a single web job URL using JobExtractor."""
        return await self.job_extractor.extract_from_url(url=url)
