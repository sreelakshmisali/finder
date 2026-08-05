"""
Query Intent Parser Service

Extracts structured SearchIntent (roles, technologies, domains, seniority, employment_type, location)
and encapsulates query parameters into a unified SearchContext container.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import re

from app.services.search.tech_taxonomy import (
    TECH_TO_DOMAINS,
    DOMAIN_TITLE_TRIGGERS,
    get_domains_for_tech
)
from app.services.search.text_normalizer import TextNormalizer
from app.services.search.role_intent_extractor import is_tech_match


@dataclass
class IntentTerm:
    """Term with confidence score for intent matching."""
    name: str
    confidence: float = 1.0

    def lower(self) -> str:
        return self.name.lower()


@dataclass
class SearchIntent:
    """Structured representation of user search intent."""
    roles: List[IntentTerm] = field(default_factory=list)
    technologies: List[IntentTerm] = field(default_factory=list)
    domains: List[IntentTerm] = field(default_factory=list)
    seniority: List[IntentTerm] = field(default_factory=list)
    employment_type: List[IntentTerm] = field(default_factory=list)
    location: List[IntentTerm] = field(default_factory=list)

    def all_keywords(self) -> List[str]:
        """Returns all term names extracted across categories."""
        terms = []
        for category in [self.roles, self.technologies, self.domains, self.seniority, self.employment_type, self.location]:
            for item in category:
                terms.append(item.name.lower())
        return terms


@dataclass
class SearchContext:
    """Unified container for query intent and search parameters."""
    raw_query: str
    intent: SearchIntent
    location: str = ""
    remote_only: bool = False
    min_salary: Optional[float] = None


# Known role categories
ROLE_DICTIONARY = {
    "developer", "engineer", "architect", "programmer", "manager", "lead", "director",
    "designer", "analyst", "administrator", "consultant", "scientist", "specialist",
    "partner", "executive", "recruiter", "coordinator"
}

# Seniority terms
SENIORITY_DICTIONARY = {"junior", "entry", "intern", "associate", "mid", "senior", "sr", "staff", "principal", "lead", "head", "vp"}


class QueryIntentParser:
    """
    Decoupled service for parsing raw search query strings into structured SearchIntent & SearchContext.
    """

    @classmethod
    def parse(
        cls,
        query: str,
        location: str = "",
        remote_only: bool = False,
        min_salary: Optional[float] = None
    ) -> SearchContext:
        """
        Parses raw user query text into a structured SearchContext using tech taxonomy.
        """
        raw_text = (query or "").strip()
        norm_q = TextNormalizer.normalize(raw_text)
        tokens = [t.lower() for t in re.findall(r'[\w\.\+\#]+', norm_q)]

        roles: List[IntentTerm] = []
        technologies: List[IntentTerm] = []
        domains: List[IntentTerm] = []
        seniority: List[IntentTerm] = []
        loc_terms: List[IntentTerm] = []

        # Sort technology terms by length descending to match multi-word techs first
        sorted_techs = sorted(TECH_TO_DOMAINS.keys(), key=lambda t: len(t), reverse=True)

        # 1. Identify Technologies & Infer Domains from Taxonomy
        for tech in sorted_techs:
            tech_norm = TextNormalizer.normalize(tech)
            if is_tech_match(tech_norm, norm_q):
                technologies.append(IntentTerm(name=tech, confidence=1.0))
                for dom in get_domains_for_tech(tech):
                    if not any(d.name == dom for d in domains):
                        domains.append(IntentTerm(name=dom, confidence=1.0))

        # 2. Identify Direct Domain Triggers
        for domain, triggers in DOMAIN_TITLE_TRIGGERS.items():
            if any(is_tech_match(tr, norm_q) for tr in triggers):
                if not any(d.name == domain for d in domains):
                    domains.append(IntentTerm(name=domain, confidence=1.0))

        # 3. Identify Roles
        for role in ROLE_DICTIONARY:
            if role in tokens:
                roles.append(IntentTerm(name=role, confidence=1.0))

        # 4. Identify Seniority
        for sen in SENIORITY_DICTIONARY:
            if sen in tokens:
                seniority.append(IntentTerm(name=sen, confidence=1.0))

        # 5. Location
        if location:
            loc_terms.append(IntentTerm(name=location.strip(), confidence=1.0))
        if remote_only or "remote" in norm_q:
            loc_terms.append(IntentTerm(name="remote", confidence=1.0))

        intent = SearchIntent(
            roles=roles,
            technologies=technologies,
            domains=domains,
            seniority=seniority,
            location=loc_terms
        )

        return SearchContext(
            raw_query=raw_text,
            intent=intent,
            location=location,
            remote_only=remote_only,
            min_salary=min_salary
        )
