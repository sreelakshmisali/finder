"""
Preferences API Endpoints

Provides REST endpoints `GET /preferences/` and `PUT /preferences/` for managing user search preferences.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.schemas.preference import PreferenceUpdate, PreferenceResponse
from app.services.preference_service import PreferenceService

router = APIRouter(prefix="/preferences", tags=["Preferences"])


@router.get(
    "/",
    response_model=PreferenceResponse,
    summary="Get user preferences",
    description="Retrieves current search preferences (preferred roles, locations, salary range, work type)."
)
async def get_preferences(db: AsyncSession = Depends(get_db)):
    """
    Get preferences endpoint.
    """
    service = PreferenceService(db)
    return await service.get_preferences()


@router.put(
    "/",
    response_model=PreferenceResponse,
    summary="Update user preferences",
    description="Updates and saves user search criteria."
)
async def update_preferences(
    payload: PreferenceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update preferences endpoint.
    """
    service = PreferenceService(db)
    return await service.save_preferences(payload)
