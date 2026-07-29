"""
Search Engine Job Discovery Provider

Unified `JobDiscoveryProvider` implementing a true multi-stage crawler pipeline:

Stage 1 — Query Enrichment:
    Raw user query → multiple targeted job-search queries
    e.g. "react" → ["react developer jobs", "site:boards.greenhouse.io react", ...]

Stage 2 — Multi-Engine Search Aggregation:
    All enriched queries run concurrently across Google / Bing / Brave / DuckDuckGo.
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
            "Google/Bing/Brave/DuckDuckGo → PageType classification → "
            "ATS/listing page drill-down → SWRR diversity scheduler → individual job extraction."
        )

    async def discover(self, context: DiscoveryContext) -> List[NormalizedJob]:
        """
        Executes the full multi-stage discovery pipeline.
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
            from app.schemas.search_metrics import SearchMetrics
            metrics = SearchMetrics()

            if tracker:
                tracker.start_stage("Stage 1 - Search Engine Discovery")

            # Stage 1 — Query enrichment
            enriched_queries = SearchQueryGenerator.generate_search_engine_queries(
                raw_query=raw_query,
                location=location,
                max_queries=15,
            )
            metrics.search_queries_generated = len(enriched_queries)

            logger.info(
                f"[SearchDiscovery] Enriched '{raw_query}' into "
                f"{len(enriched_queries)} queries"
            )
            logger.debug(
                f"\n[DEBUG - SearchDiscovery] Stage 1 complete — enriched queries:\n"
                + "\n".join(f"  • {q}" for q in enriched_queries)
            )

            # Stage 2 — Multi-engine search aggregation
            candidate_results = await self.aggregator.aggregate_multi_query(
                queries=enriched_queries,
                limit_per_query=30,
                total_limit=max(limit, 150),
            )
            candidate_urls = [r.url for r in candidate_results]
            metrics.search_results_received = len(candidate_urls)

            if tracker:
                tracker.end_stage("Stage 1 - Search Engine Discovery")
                tracker.start_stage("Stage 2 - Candidate Summary")

            logger.debug(
                f"[DEBUG - SearchDiscovery] Stage 2 complete — "
                f"{len(candidate_urls)} candidate URLs from search engines."
            )

            if tracker:
                tracker.end_stage("Stage 2 - Candidate Summary")

            if not candidate_urls:
                logger.warning("[SearchDiscovery] No candidate URLs from search engines.")
                return []

            # Stage 3 — CrawlScheduler: classify + drill down + SWRR diversity scheduler
            global_dedup = URLDeduplicator()
            tagged_urls: List[TaggedURL] = await self.scheduler.schedule(
                candidate_urls=candidate_urls,
                global_dedup=global_dedup,
                target_role=raw_query,
                candidate_results=candidate_results,
            )
            metrics.candidate_urls_scored = len(candidate_urls)
            metrics.pages_processed = len(tagged_urls)

            logger.debug(
                f"[DEBUG - SearchDiscovery] Stage 3 complete — "
                f"{len(tagged_urls)} diversity-allocated job TaggedURLs ready for extraction."
            )

            if not tagged_urls:
                logger.warning("[SearchDiscovery] CrawlScheduler allocated 0 job posting URLs.")
                return []

            # Stage 4 -- Job extraction (receives SWRR diversity-scheduled TaggedURLs, no naive truncation)
            url_to_result = {r.url: r for r in candidate_results}


            if tracker:
                tracker.start_stage("Stage 4 - Crawl/Fetching")
                tracker.start_stage("Stage 5 - Job Extraction")

            extraction_tasks = [
                self.job_extractor.extract_from_url(
                    url=tu.url,
                    search_result=tu.search_result or url_to_result.get(tu.url),
                    skip_classification=True,
                )
                for tu in tagged_urls
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
                else:
                    failures += 1

            metrics.jobs_found = len(normalized_jobs)
            metrics.jobs_invalid = failures + errors
            metrics.crawl_failures = failures + errors

            if tracker:
                tracker.end_stage("Stage 4 - Crawl/Fetching")
                tracker.end_stage("Stage 5 - Job Extraction")
                tracker.start_stage("Stage 6 - Deduplication")

            logger.info(
                f"[SearchDiscovery] Stage 4 complete: "
                f"{len(normalized_jobs)} jobs extracted, "
                f"{failures} returned None, "
                f"{errors} raised exceptions."
            )

            # Stage 5 -- Post-Extraction Ranking & Filtering
            from app.services.search.relevance_ranking import RelevanceRankingService
            ranker_service = RelevanceRankingService()

            accepted_jobs, rejected_jobs = ranker_service.rank_and_filter(
                jobs=normalized_jobs,
                query=raw_query,
                location=location or "",
                min_score=0  # Shadow mode
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

            context.metadata['search_metrics'] = metrics.model_dump()

            # Stage 6 -- Company Limiting & Deduplication
            max_jobs_per_company = self.scheduler.config.max_jobs_per_company
            company_groups = {}

            for job in accepted_jobs:
                c_name = job.company.strip().lower()
                if c_name not in company_groups:
                    company_groups[c_name] = []
                company_groups[c_name].append(job)

            import difflib

            def get_source_priority(job: NormalizedJob) -> int:
                src = job.source.lower()
                url = job.url.lower()
                if "greenhouse.io" in url or "lever.co" in url or "ashbyhq.com" in url or "workdayjobs.com" in url or "smartrecruiters.com" in url:
                    return 1
                elif "careers" in url or "company" in src:
                    return 2
                elif src == "linkedin" or "linkedin.com" in url:
                    return 4
                return 3

            final_jobs = []

            for c_name, c_jobs in company_groups.items():
                c_jobs.sort(key=get_source_priority)
                unique_jobs_for_company = []
                
                for job in c_jobs:
                    is_duplicate = False
                    for existing_job in unique_jobs_for_company:
                        title_sim = difflib.SequenceMatcher(None, job.title.lower(), existing_job.title.lower()).ratio()
                        loc_sim = difflib.SequenceMatcher(None, job.location.lower(), existing_job.location.lower()).ratio()
                        
                        if title_sim > 0.8 and loc_sim > 0.8:
                            is_duplicate = True
                            
                            # Merge logic: if we found both a LinkedIn discovery URL and a direct ATS URL
                            job_is_linkedin = "linkedin" in job.source.lower() or "linkedin.com" in job.url.lower()
                            existing_is_linkedin = "linkedin" in existing_job.source.lower() or "linkedin.com" in existing_job.url.lower()
                            
                            if job_is_linkedin and not existing_is_linkedin:
                                # existing is ATS, job is LinkedIn.
                                # User requirement: Keep source=linkedin, url=linkedin, apply_url=ATS
                                if not existing_job.apply_url:
                                    existing_job.apply_url = existing_job.url
                                existing_job.url = job.url
                                existing_job.source = "linkedin"
                                existing_job.can_apply = True
                            elif existing_is_linkedin and not job_is_linkedin:
                                # existing is LinkedIn, job is ATS.
                                # Prefer ATS apply_url
                                if job.apply_url or job.url:
                                    existing_job.apply_url = job.apply_url or job.url
                                    existing_job.can_apply = True

                            if tracker:
                                tracker.record_filtering(job.url, job.title, job.company, job.location, accepted=False, reason="Duplicate title/location fingerprint (merged)", score=job.relevance_score)
                            break
                            
                    if not is_duplicate:
                        unique_jobs_for_company.append(job)
                        
                limited = unique_jobs_for_company[:max_jobs_per_company]
                for job in unique_jobs_for_company[max_jobs_per_company:]:
                    if tracker:
                        tracker.record_filtering(job.url, job.title, job.company, job.location, accepted=False, reason=f"Company limit reached (>{max_jobs_per_company} jobs)", score=job.relevance_score)
                final_jobs.extend(limited)

            if tracker:
                tracker.end_stage("Stage 6 - Deduplication")

            # --- AGGREGATED DEBUG LOGGING ---
            if tracker:
                total_urls_discovered = len(candidate_urls)
                
                c_linkedin = 0
                c_greenhouse = 0
                c_lever = 0
                c_careers = 0
                c_other = 0
                
                rejected_classifier = 0
                skipped_domain = 0
                
                for url, info in tracker.stage3_scheduler.items():
                    if info.get("scheduled"):
                        # We don't have direct provider tags in stage3 tracker, but we can check the URL
                        if "linkedin.com" in url:
                            c_linkedin += 1
                        elif "greenhouse.io" in url:
                            c_greenhouse += 1
                        elif "lever.co" in url:
                            c_lever += 1
                        elif "careers" in url or "jobs" in url:
                            c_careers += 1
                        else:
                            c_other += 1
                    else:
                        reason = info.get("reason", "").lower()
                        if "classify" in reason or "classified as" in reason:
                            rejected_classifier += 1
                        elif "unsupported" in reason or "domain" in reason:
                            skipped_domain += 1
                
                extract_success = 0
                extract_failed = 0
                failed_categories = {}
                for url, info in tracker.stage5_extractions.items():
                    if info.get("success"):
                        extract_success += 1
                    else:
                        extract_failed += 1
                        err = info.get("error", "unknown")
                        failed_categories[err] = failed_categories.get(err, 0) + 1
                        
                duplicates_removed = len(accepted_jobs) - len(final_jobs)
                
                log_msg = f"""
Search Results:
{total_urls_discovered} URLs discovered

Classification:
LinkedIn: {c_linkedin}
Greenhouse: {c_greenhouse}
Lever: {c_lever}
Career pages: {c_careers}
Other: {c_other}
URLs rejected by classifier: {rejected_classifier}
URLs skipped due to unsupported domain: {skipped_domain}

Extraction:
Success: {extract_success}
Failed: {extract_failed}
Failure Breakdown:
"""
                for err_cat, err_count in failed_categories.items():
                    log_msg += f"  - {err_cat}: {err_count}\n"
                log_msg += f"""
Filtering & Dedup:
Rejected by Ranker: {len(rejected_jobs)}
Duplicates/Company Limit: {duplicates_removed}

Final:
{len(final_jobs)} jobs returned
"""
                logger.debug(log_msg)
                logger.info(f"Search completed: {len(final_jobs)} jobs found")

            return final_jobs
        finally:
            if token:
                current_tracker.reset(token)

    async def get_details(self, url: str) -> Optional[NormalizedJob]:
        """Fetch details for a single web job URL using JobExtractor."""
        return await self.job_extractor.extract_from_url(url=url)
