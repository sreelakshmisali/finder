"""
Role Intent Extractor Module

Extracts a structured RoleIntent (domains: Set[str], technologies: Set[str], specialization, is_generic)
from job titles, descriptions, and required skills.
Decoupled from taxonomy data and scoring algorithms.
"""

from dataclasses import dataclass, field
from typing import Set, List, Optional
import re

from app.services.search.tech_taxonomy import (
    TECH_TO_DOMAINS,
    GENERIC_ROLES,
    DOMAIN_KEYWORDS,
    get_domains_for_tech
)
from app.services.search.text_normalizer import TextNormalizer


@dataclass
class RoleIntent:
    """Structured representation of a job posting's role intent."""
    domains: Set[str] = field(default_factory=set)
    technologies: Set[str] = field(default_factory=set)
    specialization: Optional[str] = None
    is_generic: bool = False


class RoleIntentExtractor:
    """
    Extracts RoleIntent from raw job details.
    """

    @classmethod
    def extract(
        cls,
        title: str,
        desc: str = "",
        skills: Optional[List[str]] = None
    ) -> RoleIntent:
        norm_title = TextNormalizer.normalize(title or "")
        norm_desc = TextNormalizer.normalize(desc or "")
        job_skills = [TextNormalizer.normalize(s) for s in (skills or [])]

        title_tokens = set(re.findall(r'[\w\.\+\#\_]+', norm_title))

        domains: Set[str] = set()
        technologies: Set[str] = set()
        specialization: Optional[str] = None

        # 1. Check title for technologies and domains
        for tech, tech_domains in TECH_TO_DOMAINS.items():
            norm_tech = TextNormalizer.normalize(tech)
            if norm_tech in norm_title or norm_tech in title_tokens:
                technologies.add(tech)
                domains.update(tech_domains)
                if not specialization:
                    specialization = tech

        # 2. Check title for domain keywords
        for domain, keywords in DOMAIN_KEYWORDS.items():
            if any(kw in norm_title for kw in keywords):
                domains.add(domain)

        # 3. Check skills for technologies
        for sk in job_skills:
            if sk in TECH_TO_DOMAINS:
                technologies.add(sk)
                domains.update(TECH_TO_DOMAINS[sk])

        # 4. If domains are empty, infer from description
        if not domains:
            for tech, tech_domains in TECH_TO_DOMAINS.items():
                norm_tech = TextNormalizer.normalize(tech)
                if norm_tech in norm_desc:
                    technologies.add(tech)
                    domains.update(tech_domains)

        # Specialized non-generic domains
        specialized_domains = {"game", "mobile", "admin", "sales", "hr", "devops"}
        has_specialized_domain = bool(domains.intersection(specialized_domains))

        # Check if title is generic software engineering role
        is_generic_title_pattern = norm_title in GENERIC_ROLES or norm_title.strip() in {"developer", "engineer", "software engineer", "programmer"}
        is_generic = is_generic_title_pattern and not has_specialized_domain

        return RoleIntent(
            domains=domains,
            technologies=technologies,
            specialization=specialization,
            is_generic=is_generic
        )
