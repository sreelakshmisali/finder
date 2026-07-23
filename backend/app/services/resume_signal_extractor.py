"""
Resume Signal Extractor Service

Translates raw parsed resume JSON structures into a clean, normalized `ResumeSearchProfile` object.
Decouples query generation from resume parsing schema variations.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Set

from app.schemas.search_profile import ResumeSearchProfile
from app.services.tech_mappings import (
    PROGRAMMING_LANGUAGES,
    FRAMEWORKS,
    DATABASES,
    DOMAIN_KEYWORD_MAP,
    SENIORITY_KEYWORDS
)

logger = logging.getLogger(__name__)


class ResumeSignalExtractor:
    """
    Extracts structured technical and professional signals from raw resume data.
    """

    @classmethod
    def extract_profile(cls, parsed_data: Optional[Dict[str, Any]]) -> ResumeSearchProfile:
        """
        Processes a parsed resume dict and produces a normalized `ResumeSearchProfile`.

        Args:
            parsed_data: Dict representation of parsed resume fields.

        Returns:
            `ResumeSearchProfile` instance containing extracted signals.
        """
        data = parsed_data or {}

        raw_skills = cls._extract_raw_skills(data)
        roles = cls._extract_roles(data)
        years_exp = cls._extract_years_experience(data, raw_skills, roles)

        languages = cls._categorize_items(raw_skills, PROGRAMMING_LANGUAGES)
        frameworks = cls._categorize_items(raw_skills, FRAMEWORKS)
        databases = cls._categorize_items(raw_skills, DATABASES)
        domains = cls._infer_domains(raw_skills, roles)
        seniority = cls._determine_seniority(roles, years_exp)

        return ResumeSearchProfile(
            skills=raw_skills,
            primary_languages=languages,
            frameworks=frameworks,
            databases=databases,
            roles=roles,
            experience_level=seniority,
            years_experience=years_exp,
            domains=domains
        )

    @classmethod
    def _extract_raw_skills(cls, data: Dict[str, Any]) -> List[str]:
        skills: List[str] = []
        skills_field = data.get("skills", [])
        if isinstance(skills_field, list):
            for item in skills_field:
                if isinstance(item, str) and item.strip():
                    cleaned = item.strip()
                    if cleaned not in skills:
                        skills.append(cleaned)
        elif isinstance(skills_field, str):
            for item in re.split(r'[,;\n]', skills_field):
                cleaned = item.strip()
                if cleaned and cleaned not in skills:
                    skills.append(cleaned)
        return skills

    @classmethod
    def _extract_roles(cls, data: Dict[str, Any]) -> List[str]:
        roles: List[str] = []
        experience_list = data.get("experience", [])
        if isinstance(experience_list, list):
            for exp in experience_list:
                if isinstance(exp, dict):
                    title = exp.get("title") or exp.get("role") or exp.get("job_title")
                    if title and isinstance(title, str) and title.strip():
                        cleaned = title.strip()
                        if cleaned not in roles:
                            roles.append(cleaned)
                elif isinstance(exp, str) and exp.strip():
                    cleaned = exp.strip()
                    if cleaned not in roles:
                        roles.append(cleaned)
        return roles

    @classmethod
    def _categorize_items(cls, skills: List[str], target_set: Set[str]) -> List[str]:
        matches: List[str] = []
        for skill in skills:
            skill_lower = skill.lower()
            if skill_lower in target_set:
                formatted = skill.strip()
                if formatted not in matches:
                    matches.append(formatted)
        return matches

    @classmethod
    def _infer_domains(cls, skills: List[str], roles: List[str]) -> List[str]:
        domain_scores: Dict[str, int] = {}
        combined_text = " ".join(skills + roles).lower()

        for domain, keywords in DOMAIN_KEYWORD_MAP.items():
            score = 0
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', combined_text):
                    score += 1
            if score > 0:
                domain_scores[domain] = score

        if not domain_scores:
            return ["Backend"] if any("python" in s.lower() for s in skills) else ["Software"]

        sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
        return [d[0] for d in sorted_domains]

    @classmethod
    def _extract_years_experience(
        cls,
        data: Dict[str, Any],
        skills: List[str],
        roles: List[str]
    ) -> Optional[int]:
        search_text = " ".join(roles + skills)
        match = re.search(r'(\d+)\s*(?:\+|\-)?\s*(?:years?|yrs?)', search_text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass

        exp_list = data.get("experience", [])
        if isinstance(exp_list, list) and len(exp_list) > 0:
            return min(len(exp_list) * 2, 10)

        return None

    @classmethod
    def _determine_seniority(cls, roles: List[str], years: Optional[int]) -> str:
        roles_text = " ".join(roles).lower()
        for kw, level in SENIORITY_KEYWORDS.items():
            if re.search(r'\b' + re.escape(kw) + r'\b', roles_text):
                return level

        if years is not None:
            if years >= 6:
                return "Senior"
            elif years >= 3:
                return "Mid"
            elif years >= 0:
                return "Junior"

        return "Mid"
