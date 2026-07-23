"""
Matching Service

Implements the Hybrid Job Matching Engine:
1. Keyword Scoring: Computes skill overlap between candidate resume skills and job requirements.
2. Preference Bonus Alignment: Evaluates location, remote preference, role title fit, and salary targets.
3. AI Explanation: Calls `AIProvider.explain_match()` to generate human-readable reasons and recommendations.
"""

import re
import logging
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import get_ai_provider
from app.models.job import Job
from app.models.resume import Resume
from app.repositories.job_repository import JobRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.preference_repository import PreferenceRepository
from app.schemas.match import MatchResult

logger = logging.getLogger(__name__)


class MatchingService:
    """
    Service layer orchestrating hybrid job matching calculations and AI explanations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.job_repo = JobRepository(db)
        self.resume_repo = ResumeRepository(db)
        self.pref_repo = PreferenceRepository(db)
        self.ai = get_ai_provider()

    def _calculate_keyword_score(self, resume_skills: List[str], raw_text: str, job: Job) -> float:
        """
        Calculates percentage overlap between resume skills and job text.
        """
        text_to_check = f"{job.title} {job.description}".lower()
        if not resume_skills:
            words = re.findall(r"\b[a-zA-Z]{3,}\b", raw_text.lower())
            skills_to_check = set(words[:30])
        else:
            skills_to_check = set(s.lower() for s in resume_skills)

        if not skills_to_check:
            return 50.0

        matches = 0
        for skill in skills_to_check:
            if skill in text_to_check:
                matches += 1

        score = (matches / max(len(skills_to_check), 1)) * 100.0
        for skill in skills_to_check:
            if skill in job.title.lower():
                score += 15.0
                break

        return min(score, 100.0)

    def _calculate_preference_bonus(self, job: Job, preferences: Any) -> float:
        """
        Calculates preference alignment bonus (0 to 30 points).
        """
        if not preferences:
            return 15.0

        bonus = 0.0

        if preferences.work_type == "remote" and job.remote:
            bonus += 10.0
        elif preferences.preferred_locations:
            for pref_loc in preferences.preferred_locations:
                if pref_loc.lower() in job.location.lower():
                    bonus += 10.0
                    break

        if preferences.preferred_roles:
            for pref_role in preferences.preferred_roles:
                if pref_role.lower() in job.title.lower() or job.title.lower() in pref_role.lower():
                    bonus += 10.0
                    break

        if preferences.preferred_companies:
            for pref_comp in preferences.preferred_companies:
                if pref_comp.lower() in job.company.lower():
                    bonus += 10.0
                    break

        return min(bonus, 30.0)

    async def match_job(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
        resume_id: Optional[uuid.UUID] = None
    ) -> MatchResult:
        """
        Main entrypoint: matches a single job against candidate resume and preferences.
        """
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job with ID '{job_id}' not found.")

        if resume_id:
            resume = await self.resume_repo.get_by_id(resume_id, user_id)
        else:
            resume = await self.resume_repo.get_active(user_id)

        if not resume:
            return MatchResult(
                job_id=job.id,
                score=60.0,
                reasons=["Please upload a resume to calculate personalized match score."],
                missing_skills=[],
                recommendation="Upload your resume to view AI skill match breakdown.",
                score_breakdown={"keyword_score": 60.0, "preference_bonus": 0.0}
            )

        preferences = await self.pref_repo.get_preference(user_id)

        parsed_data = resume.parsed_data or {}
        resume_skills = parsed_data.get("skills", [])
        raw_text = resume.raw_text or ""

        keyword_score = self._calculate_keyword_score(resume_skills, raw_text, job)
        pref_bonus = self._calculate_preference_bonus(job, preferences)
        combined_score = round(min((keyword_score * 0.7) + pref_bonus, 98.0), 1)

        ai_explanation = await self.ai.explain_match(
            resume_data=parsed_data,
            job_title=job.title,
            company=job.company,
            job_description=job.description,
            score=combined_score
        )

        return MatchResult(
            job_id=job.id,
            score=combined_score,
            reasons=ai_explanation.get("reasons", ["Matching skills identified."]),
            missing_skills=ai_explanation.get("missing_skills", []),
            recommendation=ai_explanation.get("recommendation", f"Match score: {combined_score}%"),
            score_breakdown={
                "keyword_score": round(keyword_score, 1),
                "preference_bonus": round(pref_bonus, 1)
            }
        )

    async def batch_match_jobs(
        self,
        job_ids: List[uuid.UUID],
        user_id: uuid.UUID,
        resume_id: Optional[uuid.UUID] = None
    ) -> List[MatchResult]:
        """
        Batch matches multiple jobs for candidate in parallel.
        """
        results: List[MatchResult] = []
        for j_id in job_ids:
            try:
                res = await self.match_job(j_id, user_id, resume_id)
                results.append(res)
            except Exception as exc:
                logger.warning(f"Failed to match job '{j_id}': {exc}")

        return results
