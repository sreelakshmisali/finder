"""
Profile Service

Business logic layer managing combined user profile setup diagnostics,
merging Resume capability data and Preference goals into a single payload.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.resume_repository import ResumeRepository
from app.repositories.preference_repository import PreferenceRepository
from app.schemas.preference import PreferenceResponse
from app.schemas.profile import ProfileSetupResponse, ResumeSummary

logger = logging.getLogger(__name__)


class ProfileService:
    """
    Service layer providing unified profile setup status per candidate user.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.resume_repo = ResumeRepository(db)
        self.pref_repo = PreferenceRepository(db)

    def _extract_roles_from_parsed(self, parsed_data: Optional[Dict[str, Any]]) -> List[str]:
        """
        Extracts list of unique job roles/titles from parsed resume experience entries.
        """
        if not parsed_data:
            return []

        roles: List[str] = []
        experience_list = parsed_data.get("experience", [])
        if isinstance(experience_list, list):
            for entry in experience_list:
                if isinstance(entry, dict):
                    title = entry.get("title") or entry.get("role") or entry.get("job_title")
                    if title and isinstance(title, str) and title.strip():
                        clean_title = title.strip()
                        if clean_title not in roles:
                            roles.append(clean_title)

        return roles

    async def get_profile_setup(self, user_id: uuid.UUID) -> ProfileSetupResponse:
        """
        Builds and returns the combined profile setup status for candidate.
        """
        # 1. Fetch active resume
        active_resume = await self.resume_repo.get_active(user_id)
        resume_completed = False
        resume_summary: Optional[ResumeSummary] = None

        if active_resume:
            parsed = active_resume.parsed_data or {}
            # Resume is considered completed when active resume exists AND parsed_data is populated
            if parsed:
                resume_completed = True

            extracted_roles = self._extract_roles_from_parsed(parsed)

            resume_summary = ResumeSummary(
                has_resume=True,
                filename=active_resume.filename,
                full_name=parsed.get("full_name"),
                email=parsed.get("email"),
                phone=parsed.get("phone"),
                skills=parsed.get("skills", []),
                roles=extracted_roles,
                experience=parsed.get("experience", []),
                uploaded_at=active_resume.uploaded_at
            )

        # 2. Fetch search preferences
        pref = await self.pref_repo.get_preference(user_id)
        preferences_completed = False
        pref_response: Optional[PreferenceResponse] = None

        if pref:
            pref_response = PreferenceResponse.model_validate(pref)
            if pref.preferred_roles or pref.preferred_locations or pref.preferred_companies:
                preferences_completed = True

        # 3. Calculate completion score
        percentage = 20.0  # Base registration
        if active_resume:
            percentage += 30.0
            if active_resume.parsed_data:
                percentage += 30.0

        if preferences_completed:
            percentage += 20.0

        percentage = min(percentage, 100.0)

        return ProfileSetupResponse(
            resume_completed=resume_completed,
            preferences_completed=preferences_completed,
            profile_completion_percentage=percentage,
            resume_summary=resume_summary,
            preferences=pref_response
        )
