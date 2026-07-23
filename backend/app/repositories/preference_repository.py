"""
Preference Repository

Database access layer for Preference entity, scoped by user_id.
"""

import logging
import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.preference import Preference
from app.schemas.preference import PreferenceUpdate

logger = logging.getLogger(__name__)


class PreferenceRepository:
    """
    DAO for managing Preference records in database, scoped per user.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_preference(self, user_id: uuid.UUID) -> Optional[Preference]:
        """
        Retrieves the preference record for a specific user.
        """
        result = await self.db.execute(
            select(Preference).where(Preference.user_id == user_id).limit(1)
        )
        return result.scalars().first()

    async def create_or_update(self, user_id: uuid.UUID, update_data: PreferenceUpdate) -> Preference:
        """
        Upserts (creates or updates) the preference record for a specific user.
        """
        pref = await self.get_preference(user_id)

        if not pref:
            pref = Preference(
                user_id=user_id,
                preferred_roles=update_data.preferred_roles,
                preferred_locations=update_data.preferred_locations,
                min_salary=update_data.min_salary,
                max_salary=update_data.max_salary,
                work_type=update_data.work_type,
                preferred_companies=update_data.preferred_companies,
                experience_years=update_data.experience_years,
            )
            self.db.add(pref)
        else:
            pref.preferred_roles = update_data.preferred_roles
            pref.preferred_locations = update_data.preferred_locations
            pref.min_salary = update_data.min_salary
            pref.max_salary = update_data.max_salary
            pref.work_type = update_data.work_type
            pref.preferred_companies = update_data.preferred_companies
            pref.experience_years = update_data.experience_years

        await self.db.commit()
        await self.db.refresh(pref)
        return pref
