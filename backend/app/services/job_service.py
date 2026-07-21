"""
Job Discovery Service

Orchestrates job searches across all enabled providers concurrently using `asyncio.gather()`.
Deduplicates discovered jobs using `JobRepository` before returning normalized results.
"""

import asyncio
import logging
from typing import List, Sequence, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.providers.registry import registry
from app.repositories.job_repository import JobRepository
from app.schemas.job import JobSearchQuery, JobListResponse, JobResponse, NormalizedJob

logger = logging.getLogger(__name__)


class JobService:
    """
    Business logic orchestrator for job discovery and retrieval.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = JobRepository(db)

    async def search_jobs(self, query: JobSearchQuery) -> JobListResponse:
        """
        Executes concurrent job searches across all matching providers.

        Flow:
        1. Determine target providers (all enabled or specified subset).
        2. Run provider `search()` methods concurrently using `asyncio.gather()`.
        3. Collect all `NormalizedJob` outputs, handling exceptions gracefully.
        4. Save unique non-duplicate jobs into PostgreSQL via `JobRepository`.
        5. Query and return combined list of jobs.
        """
        all_providers = registry.get_enabled_providers()

        # Filter to requested providers if specified
        if query.providers and len(query.providers) > 0:
            target_providers = [
                p for p in all_providers if p.source_name in query.providers
            ]
        else:
            target_providers = all_providers

        searched_provider_names = [p.source_name for p in target_providers]

        if not target_providers:
            # Fallback: search stored database jobs directly
            stored_jobs = await self.repo.search_jobs(
                query=query.query,
                location=query.location,
                remote_only=query.remote_only,
                sources=query.providers,
                limit=query.limit
            )
            return JobListResponse(
                total=len(stored_jobs),
                jobs=[JobResponse.model_validate(j) for j in stored_jobs],
                providers_searched=[]
            )

        # Launch all provider searches concurrently
        tasks = [provider.search(query) for provider in target_providers]
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        raw_jobs: List[NormalizedJob] = []
        for idx, result in enumerate(results_list):
            p_name = target_providers[idx].source_name
            if isinstance(result, Exception):
                logger.error(f"Provider '{p_name}' failed with error: {result}")
            elif isinstance(result, list):
                logger.info(f"Provider '{p_name}' returned {len(result)} jobs")
                raw_jobs.extend(result)

        # Persist & deduplicate in database
        saved_db_jobs: List[Job] = []
        for norm_job in raw_jobs:
            try:
                db_job = await self.repo.save_normalized_job(norm_job)
                saved_db_jobs.append(db_job)
            except Exception as exc:
                logger.warning(f"Error saving job '{norm_job.title}' at '{norm_job.company}': {exc}")

        # If no new jobs were scraped (or network offline), query stored database jobs
        if not saved_db_jobs:
            stored = await self.repo.search_jobs(
                query=query.query,
                location=query.location,
                remote_only=query.remote_only,
                sources=query.providers,
                limit=query.limit
            )
            saved_db_jobs = list(stored)

        job_responses = [JobResponse.model_validate(j) for j in saved_db_jobs]

        return JobListResponse(
            total=len(job_responses),
            jobs=job_responses[:query.limit],
            providers_searched=searched_provider_names
        )

    async def get_job_by_id(self, job_id) -> Optional[JobResponse]:
        """
        Retrieve details for a single job by UUID.
        """
        job = await self.repo.get_by_id(job_id)
        if not job:
            return None
        return JobResponse.model_validate(job)
