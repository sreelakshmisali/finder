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

        # 1. Obtain active discovery providers
        target_providers = registry.get_enabled_providers()

        raw_candidates: List[NormalizedJob] = []

        if target_providers:
            context = DiscoveryContext(query=query, user_id=user_id)
            tasks = [provider.discover(context) for provider in target_providers]
            results_list = await asyncio.gather(*tasks, return_exceptions=True)

            for idx, result in enumerate(results_list):
                p_name = target_providers[idx].source_name
                if isinstance(result, Exception):
                    logger.error(f"Provider '{p_name}' failed: {result}")
                elif isinstance(result, list):
                    logger.info(f"Provider '{p_name}' finished: returned {len(result)} candidate jobs")
                    raw_candidates.extend(result)

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
            return JobListResponse(
                total=0,
                jobs=[],
                suggested_queries=[],
                search_mode=query.search_mode,
                applied_query=applied_query,
                applied_location=applied_location
            )

        # 2. Gatekeeper: Evaluate candidates through centralized Intent Matching Engine
        accepted_jobs, rejected_jobs = self.relevance_engine.rank_and_filter(
            jobs=raw_candidates,
            query=applied_query,
            location=applied_location,
            remote_only=query.remote_only
        )

        logger.info(
            f"[JobService] Intent Engine evaluated {len(raw_candidates)} candidates → "
            f"{len(accepted_jobs)} accepted, {len(rejected_jobs)} rejected."
        )

        # 3. Persist accepted jobs to DB
        saved_db_jobs: List[Job] = []
        for norm_job in accepted_jobs:
            try:
                db_job = await self.repo.save_normalized_job(norm_job)
                saved_db_jobs.append(db_job)
            except Exception as exc:
                logger.warning(f"Error saving job '{norm_job.title}': {exc}")

        total_elapsed = time.time() - start_time
        logger.info(f"Total relevant jobs returned: {len(saved_db_jobs)} in {total_elapsed:.2f}s")

        job_responses = [JobResponse.model_validate(j) for j in saved_db_jobs]
        return JobListResponse(
            total=len(job_responses),
            jobs=job_responses[:query.limit],
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
