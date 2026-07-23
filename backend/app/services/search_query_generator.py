"""
Search Query Generator Service

Consumes a `ResumeSearchProfile` and optional candidate `Preference` object to build
deterministic, ranked, and semantically deduplicated search queries for job discovery engines.
"""

import logging
from typing import List, Dict, Any, Optional, Set

from app.models.resume import Resume
from app.models.preference import Preference
from app.schemas.search_profile import ResumeSearchProfile, GeneratedQuery
from app.services.resume_signal_extractor import ResumeSignalExtractor

logger = logging.getLogger(__name__)


class SearchQueryGenerator:
    """
    Decoupled Search Intent Engine that converts candidate search profiles into target search queries.
    """

    @classmethod
    def generate_rich_queries(
        cls,
        profile: ResumeSearchProfile,
        preference: Optional[Preference] = None,
        max_queries: int = 5
    ) -> List[GeneratedQuery]:
        """
        Generates ranked `GeneratedQuery` objects from a candidate `ResumeSearchProfile`.

        Args:
            profile: `ResumeSearchProfile` instance.
            preference: Optional candidate search preferences entity.
            max_queries: Maximum number of query objects to return.

        Returns:
            List of `GeneratedQuery` objects sorted by priority descending.
        """
        candidates: List[GeneratedQuery] = []

        primary_lang = profile.primary_languages[0] if profile.primary_languages else ""
        if not primary_lang and profile.skills:
            primary_lang = profile.skills[0]

        primary_domain = profile.domains[0] if profile.domains else "Software"
        frameworks = profile.frameworks[:3]
        roles = profile.roles

        # Preference overrides / boosts
        pref_roles: List[str] = preference.preferred_roles if preference and preference.preferred_roles else []

        # Strategy 0: Preference Boost (if explicit preferred roles specified)
        for pref_role in pref_roles:
            if primary_lang:
                candidates.append(GeneratedQuery(
                    query=f"{primary_lang} {pref_role}".strip(),
                    priority=110,
                    strategy="preference_boost"
                ))
            else:
                candidates.append(GeneratedQuery(
                    query=pref_role.strip(),
                    priority=105,
                    strategy="preference_boost"
                ))

        # Strategy 1: Tech + Domain + Role (e.g. "Python Backend Engineer")
        if primary_lang and primary_domain:
            role_title = "Engineer"
            candidates.append(GeneratedQuery(
                query=f"{primary_lang} {primary_domain} {role_title}".strip(),
                priority=100,
                strategy="tech_domain_role"
            ))

        # Strategy 2: Framework + Role (e.g. "Django Developer", "FastAPI Engineer")
        if frameworks:
            for idx, fw in enumerate(frameworks):
                title = "Developer" if idx % 2 == 0 else "Engineer"
                candidates.append(GeneratedQuery(
                    query=f"{fw} {title}".strip(),
                    priority=90 - idx,
                    strategy="framework_role"
                ))

        # Strategy 3: Domain Specialization / API Title (e.g. "Backend API Developer")
        if primary_domain:
            has_api = any("api" in s.lower() or "rest" in s.lower() or "graphql" in s.lower() for s in profile.skills)
            spec_title = "API Developer" if has_api else "Developer"
            candidates.append(GeneratedQuery(
                query=f"{primary_domain} {spec_title}".strip(),
                priority=80,
                strategy="domain_specialization"
            ))

        # Strategy 4: Primary Language + Software Engineer (e.g. "Python Software Engineer")
        if primary_lang:
            candidates.append(GeneratedQuery(
                query=f"{primary_lang} Software Engineer".strip(),
                priority=70,
                strategy="tech_software_role"
            ))

        # Strategy 5: Previous Resume Roles
        for idx, r in enumerate(roles[:2]):
            candidates.append(GeneratedQuery(
                query=r.strip(),
                priority=65 - idx,
                strategy="resume_role"
            ))

        # Fallback Defaults if empty
        if not candidates:
            candidates = [
                GeneratedQuery(query="Backend Engineer", priority=50, strategy="default_fallback"),
                GeneratedQuery(query="Software Engineer", priority=40, strategy="default_fallback"),
                GeneratedQuery(query="Full Stack Developer", priority=30, strategy="default_fallback")
            ]

        # Sort deterministically by priority descending
        candidates.sort(key=lambda x: (-x.priority, x.query))

        # Semantic Deduplication & Token Set Filtering
        deduped: List[GeneratedQuery] = []
        seen_token_sets: List[Set[str]] = []

        for candidate in candidates:
            # Tokenize & normalize query
            tokens = set(cls._normalize_tokens(candidate.query))
            if not tokens:
                continue

            # Check if semantically subset/identical to an already accepted higher-priority query
            is_duplicate = False
            for existing_set in seen_token_sets:
                # If exact token match or 80%+ overlap
                intersection = tokens.intersection(existing_set)
                if len(intersection) == len(tokens) and len(intersection) == len(existing_set):
                    is_duplicate = True
                    break

            if not is_duplicate:
                deduped.append(candidate)
                seen_token_sets.append(tokens)

            if len(deduped) >= max_queries:
                break

        return deduped

    @classmethod
    def generate_queries(
        cls,
        resume: Optional[Resume] = None,
        preference: Optional[Preference] = None,
        max_queries: int = 5
    ) -> List[str]:
        """
        Backward-compatible helper method converting a Resume entity to plain query strings.

        Args:
            resume: Optional active Resume entity with `parsed_data`.
            preference: Optional Preference entity.
            max_queries: Maximum number of search query strings to return.

        Returns:
            List of search query strings.
        """
        parsed_data: Dict[str, Any] = (resume.parsed_data if resume else {}) or {}
        profile = ResumeSignalExtractor.extract_profile(parsed_data)
        rich_queries = cls.generate_rich_queries(profile, preference=preference, max_queries=max_queries)
        return [q.query for q in rich_queries]

    @staticmethod
    def _normalize_tokens(query_str: str) -> List[str]:
        """
        Normalizes words to canonical forms for semantic duplicate checks.
        """
        synonyms = {
            "developer": "engineer",
            "dev": "engineer",
            "programmer": "engineer",
            "coder": "engineer",
            "postgres": "postgresql",
        }
        words = query_str.lower().split()
        normalized = []
        for w in words:
            w_clean = w.strip(",.-")
            if w_clean in synonyms:
                normalized.append(synonyms[w_clean])
            else:
                normalized.append(w_clean)
        return normalized
