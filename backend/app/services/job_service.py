"""
Job Discovery Service

Orchestrates job searches across all enabled providers concurrently using `asyncio.gather()`.
Deduplicates discovered jobs using `JobRepository`, filters and ranks results via
centralized `RelevanceRankingService` Intent Matching Engine before returning normalized results.
"""

import asyncio
import logging
import time
import uuid
from typing import List, Sequence, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.providers.base_discovery import DiscoveryContext
from app.providers.registry import registry
from app.repositories.job_repository import JobRepository
from app.repositories.resume_repository import ResumeRepository
from app.services.search_query_generator import SearchQueryGenerator
from app.services.search.relevance_ranking import RelevanceRankingService
from app.schemas.job import JobSearchQuery, JobListResponse, JobResponse, NormalizedJob, SearchMode

logger = logging.getLogger(__name__)


class JobService:
    """
    Business logic orchestrator for job discovery, intent ranking, and retrieval.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = JobRepository(db)
        self.resume_repo = ResumeRepository(db)
        self.relevance_engine = RelevanceRankingService()

    async def generate_suggested_queries(self, user_id: uuid.UUID) -> List[str]:
        """
        Generates candidate search query suggestions based on active resume.
        """
        active_resume = await self.resume_repo.get_active(user_id)
        return SearchQueryGenerator.generate_queries(active_resume)

    async def search_jobs(
        self,
        query: JobSearchQuery,
        user_id: Optional[uuid.UUID] = None
    ) -> JobListResponse:
        """
        Executes job search across all enabled discovery providers concurrently,
        then evaluates all candidates through the centralized Intent Matching Engine.
        """
        start_time = time.time()
        applied_query = (query.query or "").strip()
        applied_location = (query.location or "").strip()

        from app.utils.search_diagnostics import SearchDiagnosticsTracker, current_diagnostics
        diag = SearchDiagnosticsTracker(
            query=applied_query,
            location=applied_location,
            remote_only=query.remote_only,
            limit=query.limit
        )
        diag_token = current_diagnostics.set(diag)

        # 1. Obtain active discovery providers & audit registration
        target_providers = registry.get_enabled_providers()
        registered_meta = [
            {
                "source_name": p.source_name,
                "display_name": p.display_name,
                "priority": getattr(entry, "priority", 100),
                "enabled": getattr(entry, "enabled", True)
            }
            for p in target_providers
            for entry in registry._entries.values() if entry.provider == p
        ]
        diag.audit_registered_providers(registered_meta)

        raw_candidates: List[NormalizedJob] = []
        s1_start = time.time()

        if target_providers:
            context = DiscoveryContext(query=query, user_id=user_id)
            tasks = [provider.discover(context) for provider in target_providers]
            results_list = await asyncio.gather(*tasks, return_exceptions=True)

            cumulative = 0
            for idx, result in enumerate(results_list):
                p_name = target_providers[idx].source_name
                if isinstance(result, Exception):
                    logger.error(f"Provider '{p_name}' failed: {result}")
                elif isinstance(result, list):
                    logger.info(f"Provider '{p_name}' finished: returned {len(result)} candidate jobs")
                    raw_candidates.extend(result)
                    cumulative += len(result)
                    diag.record_running_aggregation(p_name, len(result), cumulative)

        s1_dur = time.time() - s1_start
        diag.record_global_stage(
            stage_id="S1",
            stage_name="Provider Discovery & Execution",
            input_count=len(target_providers),
            output_count=len(raw_candidates),
            delta_count=0,
            duration=s1_dur
        )

        # S2: Extraction & Normalization
        diag.record_global_stage(
            stage_id="S2",
            stage_name="Extraction & Normalization",
            input_count=len(raw_candidates),
            output_count=len(raw_candidates),
            delta_count=0,
            duration=0.01
        )

        # S3: Provider-Internal Filtering
        total_p3_rejected = sum(p.p3_internal_rejected for p in diag.provider_stats.values())
        diag.record_global_stage(
            stage_id="S3",
            stage_name="Provider-Internal Filtering",
            input_count=sum(p.p2_raw_fetched for p in diag.provider_stats.values()),
            output_count=len(raw_candidates),
            delta_count=total_p3_rejected,
            duration=0.01
        )

        # Fallback to local DB if no provider returned jobs
        if not raw_candidates and (applied_query or applied_location):
            stored = await self.repo.search_jobs(
                query=applied_query,
                location=applied_location,
                remote_only=query.remote_only,
                limit=query.limit * 3,
                max_age_days=None
            )
            for db_job in stored:
                raw_candidates.append(
                    NormalizedJob(
                        company=db_job.company,
                        title=db_job.title,
                        location=db_job.location,
                        remote=db_job.remote,
                        salary=db_job.salary,
                        description=db_job.description or f"{db_job.title} position at {db_job.company}.",
                        url=db_job.url,
                        source=db_job.source,
                        apply_url=db_job.apply_url,
                        posted_date=db_job.posted_date
                    )
                )

        if not raw_candidates:
            logger.info(f"[JobService] Search completed: 0 candidates found for '{applied_query}'")
            diag.finish_session({}, {})
            current_diagnostics.reset(diag_token)
            return JobListResponse(
                total=0,
                jobs=[],
                suggested_queries=[],
                search_mode=query.search_mode,
                applied_query=applied_query,
                applied_location=applied_location
            )

        # S4: Cross-Provider Deduplication (in-memory pass before ranking)
        seen_urls = {}
        unique_pre_rank = []
        dedup_count = 0
        for job in raw_candidates:
            norm_u = job.url.strip()
            if norm_u in seen_urls:
                existing_prov = seen_urls[norm_u].source
                diag.record_deduplication_pair(existing_prov, job.source)
                dedup_count += 1
            else:
                seen_urls[norm_u] = job
                unique_pre_rank.append(job)

        diag.record_global_stage(
            stage_id="S4",
            stage_name="Cross-Provider Deduplication",
            input_count=len(raw_candidates),
            output_count=len(unique_pre_rank),
            delta_count=dedup_count,
            duration=0.01
        )

        # S5: Intent Relevance & Ranking Gatekeeper
        s5_start = time.time()
        accepted_jobs, rejected_jobs = self.relevance_engine.rank_and_filter(
            jobs=unique_pre_rank,
            query=applied_query,
            location=applied_location,
            remote_only=query.remote_only
        )
        s5_dur = time.time() - s5_start

        diag.record_global_stage(
            stage_id="S5",
            stage_name="Intent Relevance & Ranking",
            input_count=len(unique_pre_rank),
            output_count=len(accepted_jobs),
            delta_count=len(rejected_jobs),
            duration=s5_dur
        )

        logger.info(
            f"[JobService] Intent Engine evaluated {len(unique_pre_rank)} candidates → "
            f"{len(accepted_jobs)} accepted, {len(rejected_jobs)} rejected."
        )

        # Save accepted jobs to DB
        saved_db_jobs: List[Job] = []
        for norm_job in accepted_jobs:
            try:
                db_job = await self.repo.save_normalized_job(norm_job)
                saved_db_jobs.append(db_job)
            except Exception as exc:
                logger.warning(f"Error saving job '{norm_job.title}': {exc}")

        # S6: Response Limit Application
        s6_start = time.time()
        final_sliced_jobs = saved_db_jobs[:query.limit]
        s6_dur = time.time() - s6_start

        diag.record_global_stage(
            stage_id="S6",
            stage_name="Response Limit Application",
            input_count=len(saved_db_jobs),
            output_count=len(final_sliced_jobs),
            delta_count=max(len(saved_db_jobs) - len(final_sliced_jobs), 0),
            duration=s6_dur
        )

        diag.record_limit_audit(
            provider="Global Aggregator",
            location="job_service.py:L141",
            variable_name="query.limit",
            applied_limit=query.limit,
            input_size=len(saved_db_jobs),
            output_size=len(final_sliced_jobs),
            effect=f"Sliced final result list to query.limit={query.limit}"
        )

        # S7: Final API Response Construction
        s7_start = time.time()
        job_responses = [JobResponse.model_validate(j) for j in final_sliced_jobs]
        s7_dur = time.time() - s7_start

        diag.record_global_stage(
            stage_id="S7",
            stage_name="Final API Response Construction",
            input_count=len(final_sliced_jobs),
            output_count=len(job_responses),
            delta_count=0,
            duration=s7_dur
        )

        # Compute returned breakdown
        returned_urls: Dict[str, List[str]] = {}
        returned_counts: Dict[str, int] = {}
        for j in final_sliced_jobs:
            src = j.source or "unknown"
            if src not in returned_urls:
                returned_urls[src] = []
                returned_counts[src] = 0
            returned_urls[src].append(j.url)
            returned_counts[src] += 1

        diag.finish_session(returned_urls, returned_counts)
        current_diagnostics.reset(diag_token)

        total_elapsed = time.time() - start_time
        logger.info(f"Total relevant jobs returned: {len(job_responses)} in {total_elapsed:.2f}s")

        return JobListResponse(
            total=len(job_responses),
            jobs=job_responses,
            suggested_queries=[],
            search_mode=query.search_mode,
            applied_query=applied_query,
            applied_location=applied_location
        )

    async def get_job_by_id(self, job_id) -> Optional[JobResponse]:
        """
        Retrieve details for a single job by UUID.
        """
        job = await self.repo.get_by_id(job_id)
        if not job:
            return None
        return JobResponse.model_validate(job)
