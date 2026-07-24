"""
Job Discovery Service

Orchestrates job searches across all enabled providers concurrently using `asyncio.gather()`.
Deduplicates discovered jobs using `JobRepository` before returning normalized results.
"""

import asyncio
import logging
import uuid
from typing import List, Sequence, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.providers.registry import registry
from app.repositories.job_repository import JobRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.preference_repository import PreferenceRepository
from app.services.search_query_generator import SearchQueryGenerator
from app.schemas.job import JobSearchQuery, JobListResponse, JobResponse, NormalizedJob, SearchMode
from app.services.cache_service import search_cache, make_cache_key

logger = logging.getLogger(__name__)


class JobService:
    """
    Business logic orchestrator for job discovery and retrieval.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = JobRepository(db)
        self.resume_repo = ResumeRepository(db)
        self.pref_repo = PreferenceRepository(db)

    async def generate_suggested_queries(self, user_id: uuid.UUID) -> List[str]:
        """
        Generates candidate search query suggestions based on active resume and preferences.
        """
        active_resume = await self.resume_repo.get_active(user_id)
        preference = await self.pref_repo.get_preference(user_id)
        return SearchQueryGenerator.generate_queries(active_resume, preference)

    async def search_jobs(
        self,
        query: JobSearchQuery,
        user_id: Optional[uuid.UUID] = None
    ) -> JobListResponse:
        """
        Executes job search based on specified SearchMode.
        """
        suggested_queries: List[str] = []
        is_generated = False
        profile_version = "none"

        # If SMART mode, generate queries
        if user_id and query.search_mode == SearchMode.SMART:
            try:
                active_resume = await self.resume_repo.get_active(user_id)
                preference = await self.pref_repo.get_preference(user_id)
                
                # Profile version for caching
                if active_resume:
                    profile_version = str(active_resume.id)

                suggested_queries = SearchQueryGenerator.generate_queries(active_resume, preference)

                # Only use generated queries, ignore explicit user query if SMART is forced (or we could just use the first generated)
                # But the prompt says "Smart Search must only generate search queries. It must not silently inject profile preferences"
                if suggested_queries:
                    query.query = suggested_queries[0]
                    is_generated = True
                    logger.info(f"Generated SMART search query: '{query.query}' for user '{user_id}'")

            except Exception as exc:
                logger.warning(f"Failed to generate candidate query signals for user '{user_id}': {exc}")

        applied_query = query.query
        applied_location = query.location

        # Enforce search-first architecture: Do not execute empty searches.
        # A valid search must either be SMART mode OR have a query, location, or source filter.
        if query.search_mode == SearchMode.NORMAL and not query.query.strip() and not query.location.strip() and not query.providers:
            logger.info("Rejected empty NORMAL search. Returning empty result set.")
            return JobListResponse(
                total=0,
                jobs=[],
                providers_searched=[],
                suggested_queries=suggested_queries,
                search_mode=query.search_mode,
                applied_query=applied_query,
                applied_location=applied_location
            )

        cache_key = make_cache_key(
            user_id=user_id,
            query=applied_query,
            location=applied_location,
            remote_only=query.remote_only,
            providers=query.providers,
            min_salary=query.min_salary,
            limit=query.limit,
            search_mode=query.search_mode.value,
            profile_version=profile_version
        )

        # 2. Check Cache
        if not query.force_refresh:
            cached_res = await search_cache.get(cache_key)
            if cached_res:
                logger.info(f"Cache HIT for search key: '{cache_key}'")
                return cached_res

        # 3. Request Deduplication (In-Flight Lock)
        key_lock = await search_cache.get_key_lock(cache_key)
        async with key_lock:
            # Re-check cache inside lock
            if not query.force_refresh:
                cached_res = await search_cache.get(cache_key)
                if cached_res:
                    logger.info(f"Cache HIT (coalesced) for search key: '{cache_key}'")
                    return cached_res

            logger.info(f"Cache MISS for search key: '{cache_key}'. Querying Search Index...")

            from app.core.config import settings

            # 4. Check Search Index (Local Database)
            stored_jobs = await self.repo.search_jobs(
                query=query.query,
                location=query.location,
                remote_only=query.remote_only,
                sources=query.providers,
                limit=query.limit,
                max_age_days=settings.SEARCH_INDEX_MAX_JOB_AGE_DAYS
            )

            # Evaluate Quantity & Freshness
            if len(stored_jobs) >= settings.SEARCH_INDEX_MIN_RESULTS:
                logger.info(f"Search Index HIT: Found {len(stored_jobs)} fresh indexed jobs for query '{query.query}'. Skipping external discovery.")
                response = JobListResponse(
                    total=len(stored_jobs),
                    jobs=[JobResponse.model_validate(j) for j in stored_jobs],
                    providers_searched=["Indexed Jobs"],
                    suggested_queries=suggested_queries,
                    search_mode=query.search_mode,
                    applied_query=applied_query,
                    applied_location=applied_location
                )
                await search_cache.set(cache_key, response)
                await search_cache.cleanup_key_lock(cache_key)
                return response

            logger.info(f"Search Index MISS: Insufficient fresh jobs ({len(stored_jobs)}). Querying external providers...")

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
                # Fallback: return what we have in the Search Index, even if insufficient
                stored_jobs = await self.repo.search_jobs(
                    query=query.query,
                    location=query.location,
                    remote_only=query.remote_only,
                    sources=query.providers,
                    limit=query.limit,
                    max_age_days=None # Ignored for ultimate fallback
                )
                response = JobListResponse(
                    total=len(stored_jobs),
                    jobs=[JobResponse.model_validate(j) for j in stored_jobs],
                    providers_searched=[],
                    suggested_queries=suggested_queries,
                    search_mode=query.search_mode,
                    applied_query=applied_query,
                    applied_location=applied_location
                )
                await search_cache.set(cache_key, response)
                await search_cache.cleanup_key_lock(cache_key)
                return response

            # Wrap execution parameter in rich DiscoveryContext
            from app.providers.base_discovery import DiscoveryContext
            context = DiscoveryContext(query=query, user_id=user_id)

            # Launch all provider discovery tasks concurrently with isolated error handling
            tasks = [provider.discover(context) for provider in target_providers]
            results_list = await asyncio.gather(*tasks, return_exceptions=True)

            raw_jobs: List[NormalizedJob] = []
            for idx, result in enumerate(results_list):
                p_name = target_providers[idx].source_name
                if isinstance(result, Exception):
                    logger.error(f"Discovery provider '{p_name}' failed with error: {result}")
                elif isinstance(result, list):
                    logger.info(f"Discovery provider '{p_name}' returned {len(result)} jobs")
                    raw_jobs.extend(result)

            # Persist & deduplicate in Search Index
            saved_db_jobs: List[Job] = []
            for norm_job in raw_jobs:
                try:
                    db_job = await self.repo.save_normalized_job(norm_job)
                    saved_db_jobs.append(db_job)
                except Exception as exc:
                    logger.warning(f"Error saving job '{norm_job.title}' at '{norm_job.company}': {exc}")

            # If no new jobs were scraped (or network offline), query stored indexed jobs
            if not saved_db_jobs:
                stored = await self.repo.search_jobs(
                    query=query.query,
                    location=query.location,
                    remote_only=query.remote_only,
                    sources=query.providers,
                    limit=query.limit,
                    max_age_days=None # Fallback
                )
                saved_db_jobs = list(stored)

            job_responses = [JobResponse.model_validate(j) for j in saved_db_jobs]

            response = JobListResponse(
                total=len(job_responses),
                jobs=job_responses[:query.limit],
                providers_searched=searched_provider_names,
                suggested_queries=suggested_queries,
                search_mode=query.search_mode,
                applied_query=applied_query,
                applied_location=applied_location
            )

            await search_cache.set(cache_key, response)

        await search_cache.cleanup_key_lock(cache_key)
        return response

    async def get_job_by_id(self, job_id) -> Optional[JobResponse]:
        """
        Retrieve details for a single job by UUID.
        """
        job = await self.repo.get_by_id(job_id)
        if not job:
            return None
        return JobResponse.model_validate(job)
