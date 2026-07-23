"""
Resume API Endpoints

Provides REST routes for uploading PDF resumes, listing uploaded files,
toggling active resume status, and parsing resumes using AI.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.resume import ResumeResponse, ResumeListResponse
from app.services.resume_service import ResumeService
from app.services.resume_parser_service import ResumeParserService
from app.services.cache_service import search_cache

router = APIRouter(prefix="/resume", tags=["Resume"])


@router.post(
    "/upload",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload PDF resume",
    description="Uploads a PDF resume file, saves it to disk, and registers it in the database."
)
async def upload_resume(
    file: UploadFile = File(..., description="PDF file to upload"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload resume endpoint (Authenticated).
    """
    service = ResumeService(db)
    result = await service.save_resume_file(user_id=current_user.id, file=file)
    await search_cache.invalidate_user(current_user.id)
    return result


@router.get(
    "/",
    response_model=ResumeListResponse,
    summary="List uploaded resumes",
    description="Retrieves all uploaded resume entries for the current user."
)
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List resumes endpoint (Authenticated).
    """
    service = ResumeService(db)
    return await service.get_all_resumes(user_id=current_user.id)


@router.get(
    "/active",
    response_model=Optional[ResumeResponse],
    summary="Get active resume",
    description="Returns the currently active resume for the current user."
)
async def get_active_resume(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get active resume endpoint (Authenticated).
    """
    service = ResumeService(db)
    return await service.get_active_resume(user_id=current_user.id)


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    summary="Get single resume details",
    description="Retrieves resume metadata by ID for the current user."
)
async def get_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get single resume endpoint (Authenticated).
    """
    service = ResumeService(db)
    resume = await service.get_resume_by_id(resume_id=resume_id, user_id=current_user.id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID '{resume_id}' not found."
        )
    return resume


@router.patch(
    "/{resume_id}/active",
    response_model=ResumeResponse,
    summary="Set resume as active",
    description="Marks a specific resume as active for job matching."
)
async def set_active_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Set active resume endpoint (Authenticated).
    """
    service = ResumeService(db)
    result = await service.set_active_resume(resume_id=resume_id, user_id=current_user.id)
    await search_cache.invalidate_user(current_user.id)
    return result


@router.post(
    "/{resume_id}/parse",
    response_model=ResumeResponse,
    summary="Parse resume with AI",
    description="Extracts text from PDF resume and uses AI provider to parse skills, experience, and education."
)
async def parse_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Parse resume endpoint (Authenticated).
    """
    parser_service = ResumeParserService(db)
    try:
        parsed_resume = await parser_service.parse_resume(resume_id=resume_id, user_id=current_user.id)
        if not parsed_resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID '{resume_id}' not found."
            )
        await search_cache.invalidate_user(current_user.id)
        return parsed_resume
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete(
    "/{resume_id}",
    summary="Permanently delete resume",
    description="Permanently deletes PDF resume from storage disk and database."
)
async def delete_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete resume endpoint (Authenticated).
    """
    service = ResumeService(db)
    result = await service.delete_resume(resume_id=resume_id, user_id=current_user.id)
    await search_cache.invalidate_user(current_user.id)
    return result
