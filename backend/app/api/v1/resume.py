"""
Resume API Endpoints

Provides REST routes for uploading PDF resumes, listing uploaded files,
toggling active resume status, and parsing resumes using AI.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.schemas.resume import ResumeResponse, ResumeListResponse
from app.services.resume_service import ResumeService
from app.services.resume_parser_service import ResumeParserService

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
    db: AsyncSession = Depends(get_db)
):
    """
    Upload resume endpoint.
    """
    service = ResumeService(db)
    return await service.save_resume_file(file)


@router.get(
    "/",
    response_model=ResumeListResponse,
    summary="List uploaded resumes",
    description="Retrieves all uploaded resume entries."
)
async def list_resumes(db: AsyncSession = Depends(get_db)):
    """
    List resumes endpoint.
    """
    service = ResumeService(db)
    return await service.get_all_resumes()


@router.get(
    "/active",
    response_model=Optional[ResumeResponse],
    summary="Get active resume",
    description="Returns the currently active resume model."
)
async def get_active_resume(db: AsyncSession = Depends(get_db)):
    """
    Get active resume endpoint.
    """
    service = ResumeService(db)
    return await service.get_active_resume()


@router.get(
    "/{resume_id}",
    response_model=ResumeResponse,
    summary="Get single resume details",
    description="Retrieves resume metadata by ID."
)
async def get_resume(resume_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Get single resume endpoint.
    """
    service = ResumeService(db)
    resume = await service.get_resume_by_id(resume_id)
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
async def set_active_resume(resume_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Set active resume endpoint.
    """
    service = ResumeService(db)
    return await service.set_active_resume(resume_id)


@router.post(
    "/{resume_id}/parse",
    response_model=ResumeResponse,
    summary="Parse resume with AI",
    description="Extracts text from PDF resume and uses AI provider to parse skills, experience, and education."
)
async def parse_resume(resume_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Parse resume endpoint.
    """
    parser_service = ResumeParserService(db)
    try:
        parsed_resume = await parser_service.parse_resume(resume_id)
        if not parsed_resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID '{resume_id}' not found."
            )
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
    db: AsyncSession = Depends(get_db)
):
    """
    Delete resume endpoint.
    """
    service = ResumeService(db)
    return await service.delete_resume(resume_id)

