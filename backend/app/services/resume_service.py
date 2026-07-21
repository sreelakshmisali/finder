"""
Resume Service

Handles saving PDF resume files to disk storage and managing Resume database records.
"""

import os
import uuid
import logging
from typing import List, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.resume import Resume
from app.repositories.resume_repository import ResumeRepository
from app.schemas.resume import ResumeResponse, ResumeListResponse

logger = logging.getLogger(__name__)


class ResumeService:
    """
    Business logic layer for uploaded resumes.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ResumeRepository(db)
        self.upload_dir = os.path.join(settings.UPLOAD_DIR, "resumes")
        os.makedirs(self.upload_dir, exist_ok=True)

    async def save_resume_file(self, file: UploadFile) -> ResumeResponse:
        """
        Validates, saves PDF file to disk, and creates a database record.
        """
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF resume files are supported."
            )

        # Generate unique filename to avoid overwriting files with identical names
        file_ext = os.path.splitext(file.filename)[1]
        unique_name = f"{uuid.uuid4()}{file_ext}"
        saved_path = os.path.join(self.upload_dir, unique_name)

        try:
            content = await file.read()
            with open(saved_path, "wb") as f:
                f.write(content)

            db_resume = await self.repo.create(
                filename=file.filename,
                file_path=saved_path,
                is_active=True
            )
            return ResumeResponse.model_validate(db_resume)

        except Exception as exc:
            logger.error(f"Failed to save resume file: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not save resume file to disk."
            )

    async def get_all_resumes(self) -> ResumeListResponse:
        """
        Retrieves all uploaded resumes.
        """
        resumes = await self.repo.get_all()
        return ResumeListResponse(
            total=len(resumes),
            resumes=[ResumeResponse.model_validate(r) for r in resumes]
        )

    async def get_active_resume(self) -> Optional[ResumeResponse]:
        """
        Retrieves the currently active resume.
        """
        resume = await self.repo.get_active()
        if not resume:
            return None
        return ResumeResponse.model_validate(resume)

    async def get_resume_by_id(self, resume_id: uuid.UUID) -> Optional[ResumeResponse]:
        """
        Retrieves a single resume by UUID.
        """
        resume = await self.repo.get_by_id(resume_id)
        if not resume:
            return None
        return ResumeResponse.model_validate(resume)

    async def set_active_resume(self, resume_id: uuid.UUID) -> ResumeResponse:
        """
        Marks a specific resume as active.
        """
        resume = await self.repo.set_active(resume_id)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID '{resume_id}' not found."
            )
        return ResumeResponse.model_validate(resume)
