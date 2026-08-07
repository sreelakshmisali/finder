"""
Matching Service

Implements the Resume-Primary Job Matching Engine based 100% on Resume Compatibility:
- Skills match (35%)
- Experience match (20%)
- Role similarity (25%)
- Technology overlap (20%)
"""

import re
import logging
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import ranking_constants as rc

from app.ai import get_ai_provider
from app.models.job import Job
from app.models.resume import Resume
from app.repositories.job_repository import JobRepository
from app.repositories.resume_repository import ResumeRepository
from app.schemas.match import MatchResult

logger = logging.getLogger(__name__)


class MatchingService:
    """
    Service layer orchestrating job matching calculations and AI explanations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.job_repo = JobRepository(db)
        self.resume_repo = ResumeRepository(db)
        self.ai = get_ai_provider()

    def _calculate_resume_compatibility(self, parsed_data: Dict[str, Any], raw_text: str, job: Job) -> Dict[str, float]:
        """
        Calculates Resume compatibility (100% influence):
        - Skills match (35%)
        - Experience match (20%)
        - Role similarity (25%)
        - Technology overlap (20%)
        """
        job_text_lower = f"{job.title} {job.description}".lower()

        # 1. Skills Match (35%)
        resume_skills = parsed_data.get("skills", [])
        if not resume_skills and raw_text:
            words = re.findall(r"\b[a-zA-Z]{3,}\b", raw_text.lower())
            resume_skills = list(set(words[:30]))

        if resume_skills:
            matching_skills = [s for s in resume_skills if s.lower() in job_text_lower]
            skills_match = (len(matching_skills) / max(len(resume_skills), 1)) * 100.0
        else:
            skills_match = 50.0
        skills_match = min(skills_match, 100.0)

        # 2. Experience Match (20%)
        exp_levels = ["senior", "lead", "staff", "principal", "junior", "mid", "intern", "entry", "director", "manager"]
        job_exp = [level for level in exp_levels if level in job.title.lower() or level in job.description.lower()[:200]]

        resume_exp_years = parsed_data.get("experience_years")
        if not resume_exp_years:
            if "senior" in raw_text.lower() or "lead" in raw_text.lower():
                resume_exp_years = 5
            elif "junior" in raw_text.lower() or "intern" in raw_text.lower():
                resume_exp_years = 1
            else:
                resume_exp_years = 3

        if "senior" in job_exp or "lead" in job_exp or "staff" in job_exp:
            experience_match = 100.0 if resume_exp_years >= 5 else 60.0
        elif "junior" in job_exp or "intern" in job_exp or "entry" in job_exp:
            experience_match = 100.0 if resume_exp_years <= 3 else 80.0
        else:
            experience_match = 85.0

        # 3. Role Similarity (25%)
        role_similarity = 50.0
        job_title_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", job.title.lower()))
        target_roles = parsed_data.get("target_roles", []) or []
        resume_roles = [r.lower() for r in target_roles]
        if raw_text:
            resume_roles.extend(re.findall(r"\b[a-zA-Z]{3,}\b", raw_text.lower()[:300]))

        if resume_roles:
            matching_role_tokens = [w for w in job_title_words if any(w in r for r in resume_roles)]
            if matching_role_tokens:
                role_similarity = (len(matching_role_tokens) / max(len(job_title_words), 1)) * 100.0
                role_similarity = max(role_similarity, 70.0)

        role_similarity = min(max(role_similarity, 40.0), 100.0)

        # 4. Technology Overlap (20%)
        common_tech = [
            "python", "javascript", "typescript", "react", "node", "django", "fastapi", "flask",
            "docker", "kubernetes", "aws", "gcp", "azure", "sql", "postgresql", "mongodb",
            "redis", "graphql", "rest", "git", "ci/cd", "html", "css", "java", "c++", "go", "rust"
        ]
        job_tech = [t for t in common_tech if t in job_text_lower]
        if job_tech:
            matching_tech = [t for t in job_tech if t in raw_text.lower() or any(t in s.lower() for s in resume_skills)]
            tech_overlap = (len(matching_tech) / len(job_tech)) * 100.0
        else:
            tech_overlap = 80.0
        tech_overlap = min(tech_overlap, 100.0)

        raw_score = (skills_match * rc.RESUME_SKILLS_WEIGHT) + (experience_match * rc.RESUME_EXP_WEIGHT) + (role_similarity * rc.RESUME_ROLE_WEIGHT) + (tech_overlap * rc.RESUME_TECH_WEIGHT)
        raw_score = round(min(raw_score, 100.0), 1)

        return {
            "raw": raw_score,
            "weighted": round(raw_score * rc.WEIGHT_RESUME, 1),
            "skills_match": round(skills_match, 1),
            "experience_match": round(experience_match, 1),
            "role_similarity": round(role_similarity, 1),
            "tech_overlap": round(tech_overlap, 1),
        }

    async def match_job(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
        resume_id: Optional[uuid.UUID] = None
    ) -> MatchResult:
        """
        Main entrypoint: matches a single job against candidate resume.
        Resume compatibility (100% influence).
        """
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Job with ID '{job_id}' not found.")

        if resume_id:
            resume = await self.resume_repo.get_by_id(resume_id, user_id)
        else:
            resume = await self.resume_repo.get_active(user_id)

        if not resume:
            raise ValueError("Active resume is required for job matching. Please upload a PDF resume first.")

        parsed_data = resume.parsed_data or {}
        raw_text = resume.raw_text or ""

        # Calculate Resume compatibility
        resume_res = self._calculate_resume_compatibility(parsed_data, raw_text, job)
        total_score = resume_res["weighted"]

        # AI Explanation & Reason Generation
        ai_explanation = await self.ai.explain_match(
            resume_data=parsed_data,
            job_title=job.title,
            company=job.company,
            job_description=job.description,
            score=total_score
        )

        reasons = ai_explanation.get("reasons", [f"Strong alignment with {job.title} role."])
        primary_reason = reasons[0] if reasons else f"Strong {job.title} fit"
        missing_skills = ai_explanation.get("missing_skills", [])

        recommendation = ai_explanation.get(
            "recommendation",
            f"Resume Compatibility: {resume_res['raw']}%"
        )

        return MatchResult(
            job_id=job.id,
            score=total_score,
            resume_match=total_score,
            missing_skills=missing_skills,
            reason=primary_reason,
            reasons=reasons,
            recommendation=recommendation,
            score_breakdown={
                "resume_compatibility_raw": resume_res["raw"],
                "skills_match": resume_res["skills_match"],
                "experience_match": resume_res["experience_match"],
                "role_similarity": resume_res["role_similarity"],
                "tech_overlap": resume_res["tech_overlap"],
                "keyword_score": resume_res["skills_match"]
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
