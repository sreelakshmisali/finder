"""
Matching Service

Implements the Resume-Primary Hybrid Job Matching Engine:
1. Resume Compatibility (70% influence):
   - Skills match (35%)
   - Experience match (20%)
   - Role similarity (25%)
   - Technology overlap (20%)
2. Preference Alignment (30% influence):
   - Location (30%)
   - Salary (25%)
   - Remote (25%)
   - Company (20%)
3. AI Explanation & Reasoning: Calls `AIProvider.explain_match()` for human-readable reasons.
"""

import re
import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import ranking_constants as rc

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

    def _calculate_resume_compatibility(self, parsed_data: Dict[str, Any], raw_text: str, job: Job) -> Dict[str, float]:
        """
        Calculates Resume compatibility (70% influence):
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

    def _calculate_preference_alignment(self, job: Job, preferences: Any) -> Dict[str, float]:
        """
        Calculates Preference alignment (30% influence):
        - Location (30%)
        - Salary (25%)
        - Remote (25%)
        - Company (20%)
        """
        if not preferences:
            return {
                "raw": 70.0,
                "weighted": round(70.0 * rc.WEIGHT_PREFERENCE, 1),
                "location_match": 70.0,
                "salary_match": 70.0,
                "remote_match": 70.0,
                "company_match": 70.0,
            }

        # 1. Location Match (30%)
        location_match = 50.0
        if preferences.preferred_locations:
            for pref_loc in preferences.preferred_locations:
                if pref_loc.lower() in job.location.lower():
                    location_match = 100.0
                    break
        elif job.remote or "remote" in job.location.lower():
            location_match = 90.0
        else:
            location_match = 75.0

        # 2. Salary Match (25%)
        salary_match = 75.0
        if preferences.min_salary:
            if job.salary:
                numbers = re.findall(r"\d+", job.salary.replace(",", ""))
                if numbers:
                    job_sal = max(int(n) for n in numbers)
                    if job_sal >= preferences.min_salary:
                        salary_match = 100.0
                    else:
                        salary_match = 50.0
            else:
                salary_match = 75.0

        # 3. Remote Match (25%)
        remote_match = 75.0
        if preferences.work_type == "remote":
            remote_match = 100.0 if job.remote else 30.0
        elif preferences.work_type == "hybrid":
            remote_match = 85.0 if job.remote or "hybrid" in job.location.lower() else 60.0
        elif preferences.work_type == "onsite":
            remote_match = 90.0 if not job.remote else 70.0

        # 4. Company Match (20%)
        company_match = 70.0
        if preferences.preferred_companies:
            for comp in preferences.preferred_companies:
                if comp.lower() in job.company.lower():
                    company_match = 100.0
                    break
        else:
            company_match = 75.0

        raw_score = (location_match * rc.PREF_LOCATION_WEIGHT) + (salary_match * rc.PREF_SALARY_WEIGHT) + (remote_match * rc.PREF_REMOTE_WEIGHT) + (company_match * rc.PREF_COMPANY_WEIGHT)
        raw_score = round(min(raw_score, 100.0), 1)

        return {
            "raw": raw_score,
            "weighted": round(raw_score * rc.WEIGHT_PREFERENCE, 1),
            "location_match": round(location_match, 1),
            "salary_match": round(salary_match, 1),
            "remote_match": round(remote_match, 1),
            "company_match": round(company_match, 1),
        }

    def _calculate_freshness(self, job: Job) -> Dict[str, float]:
        """
        Calculates Freshness alignment (10% influence):
        - Posted Date
        - Last Verified Date / Fetched At
        """
        now = datetime.now(timezone.utc)
        
        # 1. Posted Date Score
        posted_score = 0.0
        if job.posted_date:
            posted_age = max(0.0, (now - job.posted_date).total_seconds() / 86400.0)
            # Linear decay to 0 at max days
            posted_score = max(0.0, 100.0 * (1.0 - (posted_age / rc.DECAY_POSTED_DAYS_MAX)))
            
        # 2. Verified Date Score (gracefully handles missing last_verified_date using fetched_at)
        verified_score = 0.0
        verified_date = getattr(job, 'last_verified_date', None) or job.fetched_at
        if verified_date:
            verified_age = max(0.0, (now - verified_date).total_seconds() / 86400.0)
            verified_score = max(0.0, 100.0 * (1.0 - (verified_age / rc.DECAY_VERIFIED_DAYS_MAX)))
            
        # If no posted date exists, put all weight on verification/discovery
        if not job.posted_date:
            raw_score = verified_score
        else:
            raw_score = (posted_score * rc.FRESH_POSTED_WEIGHT) + (verified_score * rc.FRESH_VERIFIED_WEIGHT)
            
        raw_score = round(min(raw_score, 100.0), 1)
        
        return {
            "raw": raw_score,
            "weighted": round(raw_score * rc.WEIGHT_FRESHNESS, 1),
            "posted_score": round(posted_score, 1),
            "verified_score": round(verified_score, 1)
        }

    async def match_job(
        self,
        job_id: uuid.UUID,
        user_id: uuid.UUID,
        resume_id: Optional[uuid.UUID] = None
    ) -> MatchResult:
        """
        Main entrypoint: matches a single job against candidate resume and preferences.
        Resume compatibility (70% influence) + Preference alignment (30% influence).
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

        preferences = await self.pref_repo.get_preference(user_id)

        parsed_data = resume.parsed_data or {}
        raw_text = resume.raw_text or ""

        # 1. Resume compatibility
        resume_res = self._calculate_resume_compatibility(parsed_data, raw_text, job)
        resume_match = resume_res["weighted"]

        # 2. Preference alignment
        pref_res = self._calculate_preference_alignment(job, preferences)
        preference_match = pref_res["weighted"]
        
        # 3. Freshness alignment
        fresh_res = self._calculate_freshness(job)
        freshness_match = fresh_res["weighted"]

        total_score = round(min(resume_match + preference_match + freshness_match, 100.0), 1)

        # 3. AI Explanation & Reason Generation
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
            f"Resume: {resume_res['raw']}% ({resume_match} pts) | Pref: {pref_res['raw']}% ({preference_match} pts) | Fresh: {fresh_res['raw']}% ({freshness_match} pts)"
        )

        return MatchResult(
            job_id=job.id,
            score=total_score,
            resume_match=resume_match,
            preference_match=preference_match,
            freshness_match=freshness_match,
            missing_skills=missing_skills,
            reason=primary_reason,
            reasons=reasons,
            recommendation=recommendation,
            score_breakdown={
                "resume_compatibility_raw": resume_res["raw"],
                "preference_alignment_raw": pref_res["raw"],
                "skills_match": resume_res["skills_match"],
                "experience_match": resume_res["experience_match"],
                "role_similarity": resume_res["role_similarity"],
                "tech_overlap": resume_res["tech_overlap"],
                "location_match": pref_res["location_match"],
                "salary_match": pref_res["salary_match"],
                "remote_match": pref_res["remote_match"],
                "company_match": pref_res["company_match"],
                "freshness_raw": fresh_res["raw"],
                "freshness_posted_score": fresh_res["posted_score"],
                "freshness_verified_score": fresh_res["verified_score"],
                "keyword_score": resume_res["skills_match"],
                "preference_bonus": preference_match,
                "freshness_bonus": freshness_match
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
