"""
Search Engine Job Discovery Provider

Unified `JobDiscoveryProvider` implementing a true multi-stage crawler pipeline:

Stage 1 — Query Enrichment:
    Raw user query → multiple targeted job-search queries
    e.g. "react" → ["react developer jobs", "site:boards.greenhouse.io react", ...]

Stage 2 — Multi-Engine Search Aggregation:
    All enriched queries run concurrently across Google / Bing / Brave / DuckDuckGo.
    Results are merged and deduplicated into a list of candidate URLs.

Stage 3 — CrawlScheduler (two-stage classification & crawl):
    Each candidate URL is classified (PageTypeClassifier) and routed:
      - JOB_POSTING       → sent directly to extraction queue
      - ATS listing page  → ATSLinkExtractor drills down to individual job URLs
      - Generic listing   → JobLinkExtractor drills down to individual job URLs
      - Blog/Docs/Home    → discarded

Stage 4 — Job Extraction:
    Only individual job posting URLs reach JobExtractor.
    JobExtractor fetches, classifies (gatekeeper), and parses each page
    into a NormalizedJob.
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

logger = logging.getLogger(__name__)


class SearchDiscoveryProvider(SearchEngineProvider):
    """
    Unified Discovery Provider for Multi-Search Engine job discovery.

    Implements a two-stage pipeline:
      Search Engines → Candidate URLs → CrawlScheduler → Job Posting URLs → JobExtractor
    """

    def __init__(
        self,
        search_providers: Optional[List[SearchProvider]] = None,
        aggregator: Optional[SearchAggregator] = None,
        job_extractor: Optional[Any] = None,
        scheduler: Optional[CrawlScheduler] = None,
    ):
        # Build aggregator from search_providers if aggregator not explicitly given
        if aggregator:
            self.aggregator = aggregator
        elif search_providers:
            self.aggregator = SearchAggregator(search_providers=search_providers)
        else:
            self.aggregator = SearchAggregator()

        self._job_extractor = job_extractor
        self._scheduler = scheduler

    # ------------------------------------------------------------------
    # Lazy properties (built on first use to keep startup fast)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # JobDiscoveryProvider interface
    # ------------------------------------------------------------------

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
            "Google/Bing/Brave/DuckDuckGo → PageType classification → "
            "ATS/listing page drill-down → individual job extraction."
        )

    async def discover(self, context: DiscoveryContext) -> List[NormalizedJob]:
        """
        Executes the full multi-stage discovery pipeline.

        Stage 1: Expand the raw query into targeted job-search queries.
        Stage 2: Run all queries across search engines, merge candidate URLs.
        Stage 3: CrawlScheduler classifies and drills down to job posting URLs.
        Stage 4: JobExtractor converts each posting URL into a NormalizedJob.
        """
        raw_query = context.query.query or "Software Engineer"
        location = context.query.location
        limit = context.query.limit

        from app.utils.pipeline_tracker import current_tracker
        tracker = current_tracker.get()
        token = None
        if not tracker:
            tracker = context.metadata.get("tracker")
            if tracker:
                token = current_tracker.set(tracker)

        try:
            # ----------------------------------------------------------------
            # Metrics Tracking Initialization
            # ----------------------------------------------------------------
            from app.schemas.search_metrics import SearchMetrics
            metrics = SearchMetrics()

            if tracker:
                tracker.start_stage("Stage 1 - Search Engine Discovery")

            # ----------------------------------------------------------------
            # Stage 1 — Query enrichment
            # ----------------------------------------------------------------
            enriched_queries = SearchQueryGenerator.generate_search_engine_queries(
                raw_query=raw_query,
                location=location,
                max_queries=15,
            )
            metrics.search_queries_generated = len(enriched_queries)
            
            logger.info(
                f"[SearchDiscovery] Enriched '{raw_query}' into "
                f"{len(enriched_queries)} queries: {enriched_queries}"
            )
            print(
                f"\n[DEBUG - SearchDiscovery] Stage 1 complete — enriched queries:\n"
                + "\n".join(f"  • {q}" for q in enriched_queries)
            )

            # ----------------------------------------------------------------
            # Stage 2 — Multi-engine search aggregation
            # ----------------------------------------------------------------
            candidate_results = await self.aggregator.aggregate_multi_query(
                queries=enriched_queries,
                limit_per_query=10,
                total_limit=limit,
            )
            candidate_urls = [r.url for r in candidate_results]
            metrics.search_results_received = len(candidate_urls)

            if tracker:
                tracker.end_stage("Stage 1 - Search Engine Discovery")
                tracker.start_stage("Stage 2 - Candidate Summary")

            print(
                f"[DEBUG - SearchDiscovery] Stage 2 complete — "
                f"{len(candidate_urls)} candidate URLs from search engines."
            )
            for u in candidate_urls:
                print(f"  • {u}")

            if tracker:
                tracker.end_stage("Stage 2 - Candidate Summary")

            if not candidate_urls:
                logger.warning("[SearchDiscovery] No candidate URLs from search engines.")
                return []

            # ----------------------------------------------------------------
            # Stage 3 — CrawlScheduler: classify + drill down
            # ----------------------------------------------------------------
            global_dedup = URLDeduplicator()
            job_posting_urls = await self.scheduler.schedule(
                candidate_urls=candidate_urls,
                global_dedup=global_dedup,
                target_role=raw_query,
            )
            metrics.candidate_urls_scored = len(candidate_urls)
            metrics.pages_processed = len(job_posting_urls)

            print(
                f"\n[DEBUG - SearchDiscovery] Stage 3 complete — "
                f"{len(job_posting_urls)} individual job posting URLs discovered."
            )
            for u in job_posting_urls:
                print(f"  • {u}")

            if not job_posting_urls:
                logger.warning("[SearchDiscovery] CrawlScheduler found no individual job posting URLs.")
                return []

            # ----------------------------------------------------------------
            # Stage 4 -- Job extraction (existing pipeline, now receives correct URLs)
            # ----------------------------------------------------------------
            # Build a lookup so we can pass SearchResult context to the extractor
            url_to_result = {r.url: r for r in candidate_results}

            print(f"\n[SearchDiscovery] Stage 4: Extracting jobs from {len(job_posting_urls[:limit])} URLs...")

            if tracker:
                tracker.start_stage("Stage 4 - Crawl/Fetching")
                tracker.start_stage("Stage 5 - Job Extraction")

            extraction_tasks = [
                self.job_extractor.extract_from_url(
                    url=url,
                    search_result=url_to_result.get(url),
                    skip_classification=True,  # CrawlScheduler already vetted these URLs
                )
                for url in job_posting_urls[:limit]
            ]
            extracted = await asyncio.gather(*extraction_tasks, return_exceptions=True)
            
            metrics.crawl_attempts = len(extraction_tasks)
            
            normalized_jobs: List[NormalizedJob] = []
            failures = 0
            errors = 0
            for i, result in enumerate(extracted):
                if isinstance(result, NormalizedJob):
                    normalized_jobs.append(result)
                elif isinstance(result, Exception):
                    errors += 1
                    print(f"[SearchDiscovery]   EXCEPTION extracting '{job_posting_urls[i]}': {result}")
                else:
                    failures += 1

            metrics.jobs_found = len(normalized_jobs)
            metrics.jobs_invalid = failures + errors
            metrics.crawl_failures = failures + errors

            if tracker:
                tracker.end_stage("Stage 4 - Crawl/Fetching")
                tracker.end_stage("Stage 5 - Job Extraction")
                tracker.start_stage("Stage 6 - Deduplication")

            print(
                f"\n[SearchDiscovery] Stage 4 complete: "
                f"{len(normalized_jobs)} jobs extracted, "
                f"{failures} returned None, "
                f"{errors} raised exceptions."
            )

            # ----------------------------------------------------------------
            # Stage 5 -- Post-Extraction Ranking & Filtering
            # ----------------------------------------------------------------
            from app.services.search.relevance_ranking import RelevanceRankingService
            ranker_service = RelevanceRankingService()
            
            # Shadow mode: set min_score=0 to not drop anything yet, but calculate scores
            # Enable enforcement by changing min_score to 50
            accepted_jobs, rejected_jobs = ranker_service.rank_and_filter(
                jobs=normalized_jobs, 
                query=raw_query, 
                location=location or "",
                min_score=0 # Shadow mode
            )
            
            if tracker:
                for job in accepted_jobs:
                    tracker.record_filtering(job.url, job.title, job.company, job.location, accepted=True, reason="Passes ranking threshold", score=job.relevance_score)
                for job in rejected_jobs:
                    tracker.record_filtering(job.url, job.title, job.company, job.location, accepted=False, reason="Below ranking threshold", score=job.relevance_score)

            metrics.calculate_aggregates(
                total_extracted=len(normalized_jobs),
                total_filtered=len(rejected_jobs),
                total_score=sum(j.relevance_score or 0 for j in accepted_jobs)
            )
            
            # Attach metrics to context metadata for logging
            context.metadata['search_metrics'] = metrics.model_dump()
            
            # ----------------------------------------------------------------
            # Stage 6 -- Company Limiting & Deduplication
            # ----------------------------------------------------------------
            max_jobs_per_company = 5
            company_groups = {}
            
            for job in accepted_jobs:
                c_name = job.company.strip().lower()
                if c_name not in company_groups:
                    company_groups[c_name] = []
                company_groups[c_name].append(job)
                
            final_jobs = []
            seen_fingerprints = set()
            
            for c_name, c_jobs in company_groups.items():
                # Jobs are already sorted by relevance (highest first) from rank_and_filter
                limited = c_jobs[:max_jobs_per_company]
                
                for job in c_jobs[max_jobs_per_company:]:
                    if tracker:
                        tracker.record_filtering(job.url, job.title, job.company, job.location, accepted=False, reason="Company limit reached (>5 jobs)", score=job.relevance_score)

                for job in limited:
                    # Deduplication fingerprint
                    title_clean = job.title.strip().lower()
                    loc_clean = job.location.strip().lower()
                    fingerprint = f"{c_name}|{title_clean}|{loc_clean}"
                    
                    if fingerprint not in seen_fingerprints:
                        seen_fingerprints.add(fingerprint)
                        final_jobs.append(job)
                    else:
                        if tracker:
                            tracker.record_filtering(job.url, job.title, job.company, job.location, accepted=False, reason="Duplicate title/location fingerprint", score=job.relevance_score)

            if tracker:
                tracker.end_stage("Stage 6 - Deduplication")

            print(
                f"\n[SearchDiscovery] Stage 5/6 complete: "
                f"{len(accepted_jobs)} jobs accepted, {len(rejected_jobs)} rejected. "
                f"After company limits & dedup: {len(final_jobs)} final jobs."
            )

            return final_jobs
        finally:
            if token:
                current_tracker.reset(token)

    async def get_details(self, url: str) -> Optional[NormalizedJob]:
        """
        Fetch details for a single web job URL using JobExtractor.
        """
        return await self.job_extractor.extract_from_url(url=url)
