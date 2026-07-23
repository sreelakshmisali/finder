"""
Preference Service

Business logic layer for retrieving and updating user job search preferences.
"""

import logging
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.preference_repository import PreferenceRepository
from app.schemas.preference import PreferenceUpdate, PreferenceResponse

logger = logging.getLogger(__name__)


class PreferenceService:
    """
    Service layer for managing candidate job search criteria.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PreferenceRepository(db)

    async def get_preferences(self, user_id: uuid.UUID) -> PreferenceResponse:
        """
        Retrieves current preferences for a user, or returns default baseline if unset.
        """
        pref = await self.repo.get_preference(user_id)
        if not pref:
            return PreferenceResponse(
                id=uuid.uuid4(),
                preferred_roles=[],
                preferred_locations=[],
                min_salary=100000,
                max_salary=180000,
                work_type="remote",
                preferred_companies=[],
                experience_years=3
            )
        return PreferenceResponse.model_validate(pref)

    async def save_preferences(self, user_id: uuid.UUID, payload: PreferenceUpdate) -> PreferenceResponse:
        """
        Saves updated search criteria for a user.
        """
        pref = await self.repo.create_or_update(user_id, payload)
        return PreferenceResponse.model_validate(pref)
