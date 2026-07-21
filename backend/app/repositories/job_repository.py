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
        Returns existing record if a duplicate URL or content hash is found.
        """
        content_hash = generate_content_hash(norm_job.company, norm_job.title, norm_job.location)

        # Check existing by content hash or URL
        existing = await self.get_by_content_hash(content_hash)
        if existing:
            return existing

        existing_url = await self.get_by_url(norm_job.url)
        if existing_url:
            return existing_url

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
