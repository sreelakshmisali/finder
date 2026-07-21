"""
Preference Service

Business logic layer for saving and retrieving user job search preferences.
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.preference_repository import PreferenceRepository
from app.schemas.preference import PreferenceUpdate, PreferenceResponse

logger = logging.getLogger(__name__)


class PreferenceService:
    """
    Business logic orchestrator for user preferences.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PreferenceRepository(db)

    async def get_preferences(self) -> PreferenceResponse:
        """
        Fetches existing preferences or creates default preference record if none exists.
        """
        pref = await self.repo.get_preference()
        if not pref:
            # Create default preference object
            default_update = PreferenceUpdate(
                preferred_roles=["Software Engineer", "Backend Engineer", "Full Stack Developer"],
                preferred_locations=["Remote", "San Francisco, CA"],
                min_salary=110000,
                max_salary=180000,
                work_type="remote",
                preferred_companies=["Stripe", "Notion", "Figma", "Linear"],
                experience_years=3
            )
            pref = await self.repo.create_or_update(default_update)
        return PreferenceResponse.model_validate(pref)

    async def save_preferences(self, update_data: PreferenceUpdate) -> PreferenceResponse:
        """
        Saves updated preference record.
        """
        pref = await self.repo.create_or_update(update_data)
        return PreferenceResponse.model_validate(pref)
