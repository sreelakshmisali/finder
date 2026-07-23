"""
Onboarding Service

Business logic service for evaluating candidate profile onboarding status,
checking active resume existence, preferences status, and calculating profile completion percentage.
"""

import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.resume_repository import ResumeRepository
from app.repositories.preference_repository import PreferenceRepository
from app.schemas.onboarding import OnboardingStatusResponse

logger = logging.getLogger(__name__)


class OnboardingService:
    """
    Service layer providing onboarding diagnostics per candidate user.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.resume_repo = ResumeRepository(db)
        self.pref_repo = PreferenceRepository(db)

    async def get_status(self, user_id: uuid.UUID) -> OnboardingStatusResponse:
        """
        Calculates onboarding status and profile completion percentage for a candidate.
        """
        # 1. Check Active Resume
        active_resume = await self.resume_repo.get_active(user_id)
        has_active_resume = active_resume is not None

        # 2. Check Preferences
        pref = await self.pref_repo.get_preference(user_id)
        has_preferences = False
        if pref:
            # Consider preferences configured if user set roles, locations, or companies
            if pref.preferred_roles or pref.preferred_locations or pref.preferred_companies:
                has_preferences = True

        resume_uploaded = has_active_resume
        resume_analyzed = bool(active_resume and active_resume.parsed_data)

        # 3. Calculate Completion Percentage
        # - Account Created: 25%
        # - Resume Uploaded: 25%
        # - Resume Analyzed: 25%
        # - Preferences Configured: 25%
        percentage = 25.0
        if resume_uploaded:
            percentage += 25.0
        if resume_analyzed:
            percentage += 25.0
        if has_preferences:
            percentage += 25.0

        return OnboardingStatusResponse(
            account_created=True,
            resume_uploaded=resume_uploaded,
            resume_analyzed=resume_analyzed,
            preferences_configured=has_preferences,
            has_active_resume=has_active_resume,
            has_preferences=has_preferences,
            profile_completion_percentage=percentage
        )
