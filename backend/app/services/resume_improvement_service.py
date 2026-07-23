"""
Resume Improvement Service

Provides business logic for AI resume quality analysis (missing skills, weak descriptions, ATS issues)
and job-specific resume suggestions without mutating candidate's original uploaded resume.
"""

import logging
import uuid
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import get_ai_provider
from app.repositories.resume_repository import ResumeRepository
from app.repositories.job_repository import JobRepository
from app.schemas.resume import (
    ResumeQualityAnalysisResponse,
    JobSpecificSuggestionsResponse,
)

logger = logging.getLogger(__name__)


class ResumeImprovementService:
    """
    Service for analyzing resume quality and generating tailored job recommendations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.resume_repo = ResumeRepository(db)
        self.job_repo = JobRepository(db)
        self.ai = get_ai_provider()

    async def analyze_quality(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> Optional[ResumeQualityAnalysisResponse]:
        """
        Runs quality audit on a resume (missing skills, weak descriptions, ATS compliance).
        """
        resume = await self.resume_repo.get_by_id(resume_id, user_id)
        if not resume:
            return None

        raw_text = resume.raw_text or ""
        parsed_data = resume.parsed_data or {}

        analysis_dict = await self.ai.analyze_resume_quality(raw_text, parsed_data)
        return ResumeQualityAnalysisResponse(**analysis_dict)

    async def suggest_job_improvements(
        self,
        resume_id: uuid.UUID,
        user_id: uuid.UUID,
        job_id: Optional[uuid.UUID] = None,
        job_title: Optional[str] = None,
        job_description: Optional[str] = None
    ) -> Optional[JobSpecificSuggestionsResponse]:
        """
        Generates job-specific resume suggestions comparing candidate resume against a target job.
        Does NOT modify the original resume in DB.
        """
        resume = await self.resume_repo.get_by_id(resume_id, user_id)
        if not resume:
            return None

        raw_text = resume.raw_text or ""
        parsed_data = resume.parsed_data or {}

        target_title = job_title or "Target Position"
        target_description = job_description or ""

        if job_id:
            db_job = await self.job_repo.get_by_id(job_id)
            if db_job:
                target_title = db_job.title
                target_description = db_job.description

        if not target_description:
            target_description = f"Job Title: {target_title}. Requires experience with software development, APIs, database design, and technical collaboration."

        suggestions_dict = await self.ai.suggest_job_specific_improvements(
            raw_text=raw_text,
            parsed_data=parsed_data,
            job_title=target_title,
            job_description=target_description
        )

        return JobSpecificSuggestionsResponse(
            job_title=target_title,
            **suggestions_dict
        )
