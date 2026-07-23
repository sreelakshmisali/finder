"""
Resume Service

Business logic layer managing PDF uploads, storage, active status toggling, and deletion.
"""

import logging
import uuid
from typing import List, Optional, Sequence
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.resume_repository import ResumeRepository
from app.schemas.resume import ResumeResponse, ResumeListResponse
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class ResumeService:
    """
    Service layer orchestrating PDF resume file management per user.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ResumeRepository(db)

    async def save_resume_file(self, user_id: uuid.UUID, file: UploadFile) -> ResumeResponse:
        """
        Saves uploaded PDF resume using StorageService, registers DB record,
        and sets as active resume for candidate.
        """
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF resume files are supported."
            )

        file_path = await StorageService.save_resume_file(user_id=user_id, file=file)

        db_resume = await self.repo.create(
            user_id=user_id,
            filename=file.filename,
            file_path=file_path,
            is_active=True
        )

        return ResumeResponse.model_validate(db_resume)

    async def get_all_resumes(self, user_id: uuid.UUID) -> ResumeListResponse:
        """
        Retrieves all uploaded resumes for a user.
        """
        resumes = await self.repo.get_all(user_id)
        responses = [ResumeResponse.model_validate(r) for r in resumes]
        return ResumeListResponse(total=len(responses), resumes=responses)

    async def get_active_resume(self, user_id: uuid.UUID) -> Optional[ResumeResponse]:
        """
        Retrieves the currently active resume for a user.
        """
        resume = await self.repo.get_active(user_id)
        if not resume:
            return None
        return ResumeResponse.model_validate(resume)

    async def get_resume_by_id(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> Optional[ResumeResponse]:
        """
        Retrieves single resume by ID for a user.
        """
        resume = await self.repo.get_by_id(resume_id=resume_id, user_id=user_id)
        if not resume:
            return None
        return ResumeResponse.model_validate(resume)

    async def set_active_resume(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> ResumeResponse:
        """
        Marks a specific resume as active for the user.
        """
        resume = await self.repo.set_active(resume_id=resume_id, user_id=user_id)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID '{resume_id}' not found."
            )
        return ResumeResponse.model_validate(resume)

    async def delete_resume(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> ResumeResponse:
        """
        Deletes resume database record and removes physical PDF file from storage.
        """
        resume = await self.repo.get_by_id(resume_id=resume_id, user_id=user_id)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID '{resume_id}' not found."
            )

        file_path_to_delete = resume.file_path

        deleted_resume = await self.repo.delete(resume_id=resume_id, user_id=user_id)
        
        # Explicit disk file deletion via StorageService abstraction
        StorageService.delete_file(file_path_to_delete)

        return ResumeResponse.model_validate(deleted_resume)
