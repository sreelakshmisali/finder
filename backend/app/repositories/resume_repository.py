"""
Resume Repository

Database access layer for Resume entities.
"""

import logging
import uuid
from typing import List, Optional, Sequence
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume

logger = logging.getLogger(__name__)


class ResumeRepository:
    """
    DAO for managing Resume records in PostgreSQL.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, filename: str, file_path: str, is_active: bool = True) -> Resume:
        """
        Creates a new Resume record. Deactivates other resumes if marked active.
        """
        if is_active:
            # Unset active status on all previous resumes
            await self.db.execute(
                update(Resume).values(is_active=False)
            )

        db_resume = Resume(
            filename=filename,
            file_path=file_path,
            is_active=is_active
        )
        self.db.add(db_resume)
        await self.db.commit()
        await self.db.refresh(db_resume)
        return db_resume

    async def get_by_id(self, resume_id: uuid.UUID) -> Optional[Resume]:
        """
        Fetch a single resume by UUID.
        """
        result = await self.db.execute(select(Resume).where(Resume.id == resume_id))
        return result.scalar_one_or_none()

    async def get_active(self) -> Optional[Resume]:
        """
        Fetch the currently active resume.
        """
        result = await self.db.execute(
            select(Resume).where(Resume.is_active.is_(True)).order_by(Resume.uploaded_at.desc())
        )
        return result.scalars().first()

    async def get_all(self) -> Sequence[Resume]:
        """
        Fetch all uploaded resumes sorted by upload date.
        """
        result = await self.db.execute(
            select(Resume).order_by(Resume.uploaded_at.desc())
        )
        return result.scalars().all()

    async def set_active(self, resume_id: uuid.UUID) -> Optional[Resume]:
        """
        Mark a specific resume as active and deactivate all others.
        """
        # Deactivate all
        await self.db.execute(update(Resume).values(is_active=False))

        # Activate target resume
        resume = await self.get_by_id(resume_id)
        if resume:
            resume.is_active = True
            await self.db.commit()
            await self.db.refresh(resume)
            return resume
        return None

    async def update_parsed_data(self, resume_id: uuid.UUID, raw_text: str, parsed_data: dict) -> Optional[Resume]:
        """
        Save extracted text and AI-parsed JSON to the resume record.
        """
        resume = await self.get_by_id(resume_id)
        if resume:
            resume.raw_text = raw_text
            resume.parsed_data = parsed_data
            await self.db.commit()
            await self.db.refresh(resume)
            return resume
        return None
