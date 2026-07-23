"""
Onboarding API Endpoints

Provides REST routes for querying user onboarding status and profile completion metrics.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.onboarding import OnboardingStatusResponse
from app.services.onboarding_service import OnboardingService

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.get(
    "/status",
    response_model=OnboardingStatusResponse,
    summary="Get onboarding completion status",
    description="Returns whether current user has an active resume, configured preferences, and profile completion percentage."
)
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Onboarding status endpoint (Authenticated).
    """
    service = OnboardingService(db)
    return await service.get_status(user_id=current_user.id)
