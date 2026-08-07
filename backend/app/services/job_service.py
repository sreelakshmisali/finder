"""
Job Discovery Service

Orchestrates job searches across all enabled providers concurrently using `asyncio.gather()`.
Deduplicates discovered jobs using `JobRepository` before returning normalized results.
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
from app.schemas.job import JobSearchQuery, JobListResponse, JobResponse, NormalizedJob, SearchMode

logger = logging.getLogger(__name__)


class JobService:
    """
    Business logic orchestrator for job discovery and retrieval.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = JobRepository(db)
        self.resume_repo = ResumeRepository(db)

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
        Executes job search across all enabled discovery providers concurrently.
        """
        start_time = time.time()
        applied_query = query.query or ""
        applied_location = query.location or ""

        # logger.info(f"Search started: query='{applied_query}', location='{applied_location}'")

        # 1. Obtain active providers
        target_providers = registry.get_enabled_providers()

        if not target_providers:
            logger.warning("No discovery providers enabled.")
            stored_jobs = await self.repo.search_jobs(
                query=applied_query,
                location=applied_location,
                remote_only=query.remote_only,
                limit=query.limit
            )
            return JobListResponse(
                total=len(stored_jobs),
                jobs=[JobResponse.model_validate(j) for j in stored_jobs],
                suggested_queries=[],
                search_mode=query.search_mode,
                applied_query=applied_query,
                applied_location=applied_location
            )

        # 2. Execute providers concurrently
        context = DiscoveryContext(query=query, user_id=user_id)
        tasks = [provider.discover(context) for provider in target_providers]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        raw_jobs: List[NormalizedJob] = []
        for idx, result in enumerate(results_list):
            p_name = target_providers[idx].source_name
            if isinstance(result, Exception):
                logger.error(f"Provider '{p_name}' failed: {result}")
            elif isinstance(result, list):
                logger.info(f"Provider '{p_name}' finished: returned {len(result)} jobs")
                raw_jobs.extend(result)

        # 3. Persist & normalize results in DB
        saved_db_jobs: List[Job] = []
        for norm_job in raw_jobs:
            try:
                db_job = await self.repo.save_normalized_job(norm_job)
                saved_db_jobs.append(db_job)
            except Exception as exc:
                logger.warning(f"Error saving job '{norm_job.title}': {exc}")

        # Fallback to local DB if 0 new jobs returned
        if not saved_db_jobs and (applied_query or applied_location):
            stored = await self.repo.search_jobs(
                query=applied_query,
                location=applied_location,
                remote_only=query.remote_only,
                limit=query.limit,
                max_age_days=None
            )
            saved_db_jobs = list(stored)

        total_elapsed = time.time() - start_time
        logger.info(f"Total jobs saved to DB: {len(saved_db_jobs)} in {total_elapsed:.2f}s")

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
