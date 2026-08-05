"""
Role Intent Extractor Service

Extracts structured RoleIntent (domains set, technologies set, specialization, is_generic)
from job title, description, and required skills.
"""

from dataclasses import dataclass, field
from typing import Set, Optional, List
import re

from app.services.search.tech_taxonomy import (
    TECH_TO_DOMAINS,
    DOMAIN_TITLE_TRIGGERS,
    GENERIC_ROLES,
    get_domains_for_tech
)
from app.services.search.text_normalizer import TextNormalizer


@dataclass
class RoleIntent:
    """Structured intent representation of a job posting."""
    domains: Set[str] = field(default_factory=set)
    technologies: Set[str] = field(default_factory=set)
    specialization: Optional[str] = None
    is_generic: bool = False


def is_tech_match(tech_norm: str, text: str) -> bool:
    """Checks exact technology word match excluding word/underscore bounds."""
    pattern = r'(?<![\w_])' + re.escape(tech_norm) + r'(?![\w_])'
    return bool(re.search(pattern, text))


class RoleIntentExtractor:
    """
    Dedicated extractor transforming job titles, descriptions, and skills into structured RoleIntent.
    """

    @classmethod
    def extract(cls, title: str, desc: str = "", skills: Optional[List[str]] = None) -> RoleIntent:
        """
        Extracts RoleIntent from job posting content.
        """
        norm_title = TextNormalizer.normalize(title or "")
        norm_desc = TextNormalizer.normalize(desc or "")
        job_skills = [TextNormalizer.normalize(s) for s in (skills or [])]

        domains: Set[str] = set()
        technologies: Set[str] = set()
        specialization: Optional[str] = None

        # Sort technology terms by length descending to match multi-word techs (e.g. react_native) before single-word techs (react)
        sorted_techs = sorted(TECH_TO_DOMAINS.keys(), key=lambda t: len(t), reverse=True)

        # 1. Identify Technologies in title, skills, and description
        for tech in sorted_techs:
            tech_norm = TextNormalizer.normalize(tech)
            in_title = is_tech_match(tech_norm, norm_title)
            in_skills = any(is_tech_match(tech_norm, sk) for sk in job_skills)
            in_desc = is_tech_match(tech_norm, norm_desc)

            if in_title:
                technologies.add(tech)
                domains.update(get_domains_for_tech(tech))
                if not specialization:
                    specialization = tech
            elif in_skills or in_desc:
                technologies.add(tech)
                domains.update(get_domains_for_tech(tech))

        # 2. Identify Title Domain Triggers
        for domain, triggers in DOMAIN_TITLE_TRIGGERS.items():
            if any(is_tech_match(tr, norm_title) for tr in triggers):
                domains.add(domain)
                if not specialization:
                    specialization = domain

        # Special check for Full Stack
        if "fullstack" in norm_title or "full stack" in norm_title:
            domains.update({"frontend", "backend"})

        # 3. Determine if Generic Software Engineering Title
        title_techs = {t for t in TECH_TO_DOMAINS if is_tech_match(TextNormalizer.normalize(t), norm_title)}
        title_domain_triggers = any(any(is_tech_match(tr, norm_title) for tr in triggers) for d, triggers in DOMAIN_TITLE_TRIGGERS.items() if d != "management")

        is_generic = not (bool(title_techs) or title_domain_triggers)

        return RoleIntent(
            domains=domains,
            technologies=technologies,
            specialization=specialization,
            is_generic=is_generic
        )
