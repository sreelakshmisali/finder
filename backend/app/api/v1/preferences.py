"""
Preferences API Endpoints

Provides REST endpoints `GET /preferences/` and `PUT /preferences/` for managing user search preferences.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.preference import PreferenceUpdate, PreferenceResponse
from app.services.preference_service import PreferenceService

router = APIRouter(prefix="/preferences", tags=["Preferences"])


@router.get(
    "/",
    response_model=PreferenceResponse,
    summary="Get user preferences",
    description="Retrieves current search preferences (preferred roles, locations, salary range, work type)."
)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get preferences endpoint (Authenticated).
    """
    service = PreferenceService(db)
    return await service.get_preferences(user_id=current_user.id)


@router.put(
    "/",
    response_model=PreferenceResponse,
    summary="Update user preferences",
    description="Updates and saves user search criteria."
)
async def update_preferences(
    payload: PreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update preferences endpoint (Authenticated).
    """
    service = PreferenceService(db)
    return await service.save_preferences(user_id=current_user.id, payload=payload)
