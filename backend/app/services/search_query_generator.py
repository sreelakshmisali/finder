"""
Search Query Generator Service

Generates targeted job search query strings based on candidate active resume skills
and optional job search preferences.
"""

import logging
from typing import List, Dict, Any, Optional

from app.models.resume import Resume
from app.models.preference import Preference

logger = logging.getLogger(__name__)


class SearchQueryGenerator:
    """
    Utility service for constructing candidate-aware job search query strings.
    """

    @staticmethod
    def generate_queries(
        resume: Optional[Resume] = None,
        preference: Optional[Preference] = None,
        max_queries: int = 5
    ) -> List[str]:
        """
        Generates a list of relevant search query strings.

        Args:
            resume: Optional active Resume entity with `parsed_data`.
            preference: Optional Preference entity.
            max_queries: Maximum number of query strings to return.

        Returns:
            List of generated search query strings (e.g. ['Python Backend', 'FastAPI Developer']).
        """
        parsed_data: Dict[str, Any] = (resume.parsed_data if resume else {}) or {}

        # 1. Extract skills
        skills: List[str] = []
        if isinstance(parsed_data.get("skills"), list):
            skills = [s.strip() for s in parsed_data["skills"] if isinstance(s, str) and s.strip()]

        # 2. Extract roles/titles from resume experience
        resume_roles: List[str] = []
        experience_list = parsed_data.get("experience", [])
        if isinstance(experience_list, list):
            for exp in experience_list:
                if isinstance(exp, dict):
                    title = exp.get("title") or exp.get("role") or exp.get("job_title")
                    if title and isinstance(title, str) and title.strip():
                        clean_title = title.strip()
                        if clean_title not in resume_roles:
                            resume_roles.append(clean_title)

        # 3. Extract preferred roles & work mode from Preference
        pref_roles: List[str] = preference.preferred_roles if preference and preference.preferred_roles else []

        # Combine role candidates
        all_roles = pref_roles + resume_roles
        if not all_roles:
            all_roles = ["Developer", "Engineer", "Software Engineer"]

        queries: List[str] = []

        # Strategy A: Pair top skills with role titles (e.g., 'Python Backend', 'FastAPI Engineer')
        if skills:
            top_skills = skills[:4]
            primary_role = all_roles[0] if all_roles else "Engineer"

            for skill in top_skills:
                combo = f"{skill} {primary_role}".strip()
                if combo not in queries:
                    queries.append(combo)
                # Also add standalone skill if distinct
                if skill not in queries and len(skill) > 2:
                    queries.append(f"{skill} Developer")

        # Strategy B: Use preferred or extracted roles directly
        for role in all_roles[:3]:
            if role not in queries:
                queries.append(role)

        # Fallback default if nothing extracted
        if not queries:
            queries = ["Software Engineer", "Backend Developer", "Full Stack Engineer"]

        # Deduplicate & cap to max_queries
        unique_queries: List[str] = []
        for q in queries:
            if q not in unique_queries:
                unique_queries.append(q)
            if len(unique_queries) >= max_queries:
                break

        return unique_queries
