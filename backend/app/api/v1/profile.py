"""
Profile API Endpoints

Provides REST routes for querying combined profile setup details (Resume capability + Preference goals).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.profile import ProfileSetupResponse
from app.services.profile_service import ProfileService

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
