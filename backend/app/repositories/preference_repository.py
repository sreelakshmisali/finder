"""
Preference Repository

Database access layer for Preference entity.
"""

import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.preference import Preference
from app.schemas.preference import PreferenceUpdate

logger = logging.getLogger(__name__)


class PreferenceRepository:
    """
    DAO for managing Preference records in database.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_preference(self) -> Optional[Preference]:
        """
        Retrieves the single preference record.
        """
        result = await self.db.execute(select(Preference).limit(1))
        return result.scalars().first()

    async def create_or_update(self, update_data: PreferenceUpdate) -> Preference:
        """
        Upserts (creates or updates) the preference record.
        """
        pref = await self.get_preference()

        if not pref:
            pref = Preference(
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
