"""
Onboarding Service

Business logic service for evaluating candidate profile onboarding status,
checking active resume existence, and calculating profile completion percentage.
"""

import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.resume_repository import ResumeRepository
from app.schemas.onboarding import OnboardingStatusResponse

logger = logging.getLogger(__name__)


class OnboardingService:
    """
    Service layer providing onboarding diagnostics per candidate user.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.resume_repo = ResumeRepository(db)

    async def get_status(self, user_id: uuid.UUID) -> OnboardingStatusResponse:
        """
        Calculates onboarding status and profile completion percentage for a candidate.
        """
        # 1. Check Active Resume
        active_resume = await self.resume_repo.get_active(user_id)
        has_active_resume = active_resume is not None

        resume_uploaded = has_active_resume
        resume_analyzed = bool(active_resume and active_resume.parsed_data)

        # 2. Calculate Completion Percentage
        # - Account Created: 34%
        # - Resume Uploaded: 33%
        # - Resume Analyzed: 33%
        percentage = 34.0
        if resume_uploaded:
            percentage += 33.0
        if resume_analyzed:
            percentage += 33.0

        return OnboardingStatusResponse(
            account_created=True,
            resume_uploaded=resume_uploaded,
            resume_analyzed=resume_analyzed,
            has_active_resume=has_active_resume,
            profile_completion_percentage=percentage
        )
