"""
Job Repository

Database access layer for Job entities.
Encapsulates all direct SQLAlchemy database queries for creating, retrieving,
and deduplicating jobs.
"""

import logging
from typing import List, Optional, Sequence
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.schemas.job import NormalizedJob
from app.utils.dedup import generate_content_hash
from app.services.dedup import DuplicateDetectionService

logger = logging.getLogger(__name__)


class JobRepository:
    """
    Data Access Object (DAO) for Jobs.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, job_id) -> Optional[Job]:
        """
        Fetch a single job by UUID.
        """
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()

    async def get_by_url(self, url: str) -> Optional[Job]:
        """
        Fetch a job by its unique URL.
        """
        result = await self.db.execute(select(Job).where(Job.url == url))
        return result.scalar_one_or_none()

    async def get_by_content_hash(self, content_hash: str) -> Optional[Job]:
        """
        Fetch an existing job matching the specified content hash.
        """
        result = await self.db.execute(select(Job).where(Job.content_hash == content_hash))
        return result.scalar_one_or_none()

    async def save_normalized_job(self, norm_job: NormalizedJob) -> Job:
        """
        Converts a NormalizedJob schema to a Job DB record and saves it if not a duplicate.
        Returns existing merged record if a duplicate is found using intelligent detection.
        """
        content_hash = generate_content_hash(norm_job.company, norm_job.title, norm_job.location)
        from app.utils.pipeline_tracker import current_tracker
        tracker = current_tracker.get()

        from app.utils.search_diagnostics import current_diagnostics
        diag = current_diagnostics.get()

        # 1. Exact URL match (fast path)
        existing_url = await self.get_by_url(norm_job.url)
        if existing_url:
            if tracker:
                tracker.record_persistence(norm_job.url, status="merged", duplicate_of_url=existing_url.url, details="Exact URL match")
            if diag:
                diag.record_deduplication(
                    losing_job_url=norm_job.url,
                    surviving_job_url=existing_url.url,
                    losing_provider=norm_job.source,
                    surviving_provider=existing_url.source,
                    rule_triggered="exact_url_match"
                )
            return await self._merge_job(existing_url, norm_job)

        # 2. Exact content hash match (legacy fast path)
        existing_hash = await self.get_by_content_hash(content_hash)
        if existing_hash:
            if tracker:
                tracker.record_persistence(norm_job.url, status="merged", duplicate_of_url=existing_hash.url, details="Exact title/company/location content hash match")
            if diag:
                diag.record_deduplication(
                    losing_job_url=norm_job.url,
                    surviving_job_url=existing_hash.url,
                    losing_provider=norm_job.source,
                    surviving_provider=existing_hash.source,
                    rule_triggered="exact_content_hash_match"
                )
            return await self._merge_job(existing_hash, norm_job)

        # 3. Intelligent Duplicate Detection
        dedup_service = DuplicateDetectionService()
        
        # Fetch candidates: similar company, recent
        # Extract a prefix or normalized term to query
        norm_company = dedup_service.normalize_string(norm_job.company)
        search_term = norm_company[:10] if len(norm_company) > 10 else norm_company
        
        stmt = select(Job).where(Job.company.ilike(f"%{search_term}%")).order_by(Job.posted_date.desc()).limit(50)
        result = await self.db.execute(stmt)
        candidates = result.scalars().all()

        dup_result = dedup_service.detect_duplicate(norm_job, candidates)
        if dup_result.is_duplicate and dup_result.duplicate_of_id:
            existing_dup = await self.get_by_id(dup_result.duplicate_of_id)
            if existing_dup:
                if tracker:
                    tracker.record_persistence(norm_job.url, status="merged", duplicate_of_url=existing_dup.url, details=f"Similarity duplicate match (score={dup_result.score:.2f})")
                if diag:
                    diag.record_deduplication(
                        losing_job_url=norm_job.url,
                        surviving_job_url=existing_dup.url,
                        losing_provider=norm_job.source,
                        surviving_provider=existing_dup.source,
                        rule_triggered=f"intelligent_similarity_match(score={dup_result.score:.2f})"
                    )
                return await self._merge_job(existing_dup, norm_job)

        # 4. No duplicate found, create new record

        db_job = Job(
            company=norm_job.company,
            title=norm_job.title,
            location=norm_job.location,
            remote=norm_job.remote,
            salary=norm_job.salary,
            description=norm_job.description,
            url=norm_job.url,
            source=norm_job.source,
            discovery_provider=norm_job.discovery_provider or norm_job.source,
            apply_url=norm_job.apply_url,
            can_apply=norm_job.can_apply,
            content_hash=content_hash,
            posted_date=norm_job.posted_date,
        )

        self.db.add(db_job)
        await self.db.commit()
        await self.db.refresh(db_job)
        if tracker:
            tracker.record_persistence(norm_job.url, status="new", details="Unique job saved successfully")
        return db_job

    async def _merge_job(self, existing: Job, norm_job: NormalizedJob) -> Job:
        """
        Merges missing metadata from a newly fetched duplicate job into the existing database record.
        """
        changed = False

        # Merge salary if existing is missing it
        if not existing.salary and norm_job.salary:
            existing.salary = norm_job.salary
            changed = True
            
        # Merge remote flag (e.g. if one source didn't tag it but the other did)
        if not existing.remote and norm_job.remote:
            existing.remote = True
            changed = True
            
        # Append source if new — cap at column length (String 50) to prevent overflow.
        # sources are short identifiers like "greenhouse", "lever", "search_engine".
        if norm_job.source not in existing.source:
            combined = f"{existing.source},{norm_job.source}"
            existing.source = combined[:50]
            changed = True
            
        # Merge apply_url and can_apply if existing is missing it
        if not existing.apply_url and norm_job.apply_url:
            existing.apply_url = norm_job.apply_url
            existing.can_apply = norm_job.can_apply
            changed = True
            
        # Keep URL if we want to prefer LinkedIn, but since search_discovery already handles logic, just inherit apply_url
        if existing.source == "linkedin" and existing.apply_url:
            existing.can_apply = True

        if changed:
            await self.db.commit()
            await self.db.refresh(existing)
            
        return existing

    async def search_jobs(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        remote_only: bool = False,
        limit: int = 50,
        max_age_days: Optional[int] = None
    ) -> Sequence[Job]:
        """
        Search indexed jobs in PostgreSQL matching keywords or location filters.
        """
        stmt = select(Job)

        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    Job.title.ilike(pattern),
                    Job.company.ilike(pattern),
                    Job.description.ilike(pattern)
                )
            )

        if location:
            stmt = stmt.where(Job.location.ilike(f"%{location}%"))

        if remote_only:
            stmt = stmt.where(Job.remote.is_(True))

        # Enforce linkedin_mode config filter in database searches
        from app.core.scheduler_config import SchedulerConfig
        config = SchedulerConfig.from_env()
        if config.linkedin_mode == "external_only":
            stmt = stmt.where(
                or_(
                    Job.source.is_(None),
                    ~Job.source.ilike("%linkedin%"),
                    Job.can_apply.is_(True)
                )
            )

        if max_age_days is not None:
            from datetime import datetime, timedelta, timezone
            cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
            stmt = stmt.where(Job.posted_date >= cutoff)

        stmt = stmt.order_by(Job.posted_date.desc()).limit(limit)

        result = await self.db.execute(stmt)
        return result.scalars().all()
