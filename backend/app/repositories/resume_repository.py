"""
Resume Repository

Database access layer for Resume entities, scoped by user_id.
"""

import logging
import uuid
from typing import List, Optional, Sequence
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume

logger = logging.getLogger(__name__)


class ResumeRepository:
    """
    DAO for managing Resume records in PostgreSQL.
    All operations are strictly scoped by user_id.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: uuid.UUID, filename: str, file_path: str, is_active: bool = True) -> Resume:
        """
        Creates a new Resume record for the specified user.
        Deactivates other resumes owned by the SAME user if marked active.
        """
        if is_active:
            # Unset active status on all previous resumes for THIS user
            await self.db.execute(
                update(Resume)
                .where(Resume.user_id == user_id)
                .values(is_active=False)
            )

        db_resume = Resume(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            is_active=is_active
        )
        self.db.add(db_resume)
        await self.db.commit()
        await self.db.refresh(db_resume)
        return db_resume

    async def get_by_id(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Resume]:
        """
        Fetch a single resume by UUID and user_id.
        """
        result = await self.db.execute(
            select(Resume).where(and_(Resume.id == resume_id, Resume.user_id == user_id))
        )
        return result.scalar_one_or_none()

    async def get_active(self, user_id: uuid.UUID) -> Optional[Resume]:
        """
        Fetch the currently active resume for a user.
        """
        result = await self.db.execute(
            select(Resume)
            .where(and_(Resume.user_id == user_id, Resume.is_active.is_(True)))
            .order_by(Resume.uploaded_at.desc())
        )
        return result.scalars().first()

    async def get_all(self, user_id: uuid.UUID) -> Sequence[Resume]:
        """
        Fetch all uploaded resumes for a user sorted by upload date.
        """
        result = await self.db.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.uploaded_at.desc())
        )
        return result.scalars().all()

    async def set_active(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Resume]:
        """
        Mark a specific resume as active and deactivate all others owned by the user.
        """
        # Deactivate all for user
        await self.db.execute(
            update(Resume).where(Resume.user_id == user_id).values(is_active=False)
        )

        # Activate target resume
        resume = await self.get_by_id(resume_id, user_id)
        if resume:
            resume.is_active = True
            await self.db.commit()
            await self.db.refresh(resume)
            return resume
        return None

    async def update_parsed_data(
        self,
        resume_id: uuid.UUID,
        user_id: uuid.UUID,
        raw_text: str,
        parsed_data: dict
    ) -> Optional[Resume]:
        """
        Save extracted text and AI-parsed JSON to the user's resume record.
        """
        resume = await self.get_by_id(resume_id, user_id)
        if resume:
            resume.raw_text = raw_text
            resume.parsed_data = parsed_data
            await self.db.commit()
            await self.db.refresh(resume)
            return resume
        return None

    async def get_count(self, user_id: uuid.UUID) -> int:
        """
        Count total number of resume records for a user.
        """
        resumes = await self.get_all(user_id)
        return len(resumes)

    async def delete(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Resume]:
        """
        Permanently deletes a resume database record for a user.
        If the deleted resume was active, promotes the user's next most recent resume to active.
        """
        resume = await self.get_by_id(resume_id, user_id)
        if not resume:
            return None

        was_active = resume.is_active

        await self.db.delete(resume)
        await self.db.commit()

        if was_active:
            # Promote most recent remaining resume for user to active
            remaining = await self.get_all(user_id)
            if remaining:
                next_active = remaining[0]
                next_active.is_active = True
                await self.db.commit()

        return resume
