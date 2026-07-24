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

        # 1. Exact URL match (fast path)
        existing_url = await self.get_by_url(norm_job.url)
        if existing_url:
            return await self._merge_job(existing_url, norm_job)

        # 2. Exact content hash match (legacy fast path)
        existing_hash = await self.get_by_content_hash(content_hash)
        if existing_hash:
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
            content_hash=content_hash,
            posted_date=norm_job.posted_date,
        )

        self.db.add(db_job)
        await self.db.commit()
        await self.db.refresh(db_job)
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
            
        # Append source if new
        if norm_job.source not in existing.source:
            existing.source = f"{existing.source},{norm_job.source}"
            changed = True
            
        if changed:
            await self.db.commit()
            await self.db.refresh(existing)
            
        return existing

    async def search_jobs(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        remote_only: bool = False,
        sources: Optional[List[str]] = None,
        limit: int = 50
    ) -> Sequence[Job]:
        """
        Search stored jobs in PostgreSQL matching keywords, location, or source filters.
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

        if sources and len(sources) > 0:
            stmt = stmt.where(Job.source.in_(sources))

        stmt = stmt.order_by(Job.posted_date.desc()).limit(limit)

        result = await self.db.execute(stmt)
        return result.scalars().all()
