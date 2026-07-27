"""
Profile API Endpoints

Provides REST routes for querying combined profile setup details (Resume capability + Preference goals).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.profile import ProfileSetupResponse
from app.services.profile_service import ProfileService
from app.services.resume_service import ResumeService

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get(
    "/setup",
    response_model=ProfileSetupResponse,
    summary="Get combined profile setup status",
    description="Returns resume completion status, extracted resume summary, search preferences, and completion percentage."
)
async def get_profile_setup(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get profile setup endpoint (Authenticated).
    """
    service = ProfileService(db)
    return await service.get_profile_setup(user_id=current_user.id)


@router.get(
    "/resume/view",
    summary="View active resume PDF",
    description="Returns the currently active resume PDF file for the authenticated user inline."
)
async def view_active_resume(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    View active resume endpoint (Authenticated).
    """
    resume_service = ResumeService(db)
    active_resume = await resume_service.get_active_resume(user_id=current_user.id)
    
    if not active_resume or not active_resume.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active resume found for viewing."
        )
    
    if not os.path.exists(active_resume.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active resume file is missing or corrupted."
        )
        
    return FileResponse(
        path=active_resume.file_path,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{active_resume.filename}"'}
    )
