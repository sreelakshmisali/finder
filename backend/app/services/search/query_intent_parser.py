"""
Query Intent Parser Service

Extracts structured SearchIntent (roles, technologies, domains, seniority, employment_type, location)
and encapsulates query parameters into a unified SearchContext container.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import re


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


# Known technology mappings
TECH_DICTIONARY = {
    "react", "react.js", "reactjs", "next.js", "nextjs", "vue", "vue.js", "angular", "angularjs",
    "python", "django", "fastapi", "flask", "java", "spring", "spring boot", "node", "node.js", "nodejs",
    "typescript", "javascript", "golang", "go", "ruby", "rails", "c#", ".net", "rust", "c++",
    "sql", "postgresql", "postgres", "mongodb", "aws", "docker", "kubernetes", "k8s", "graphql"
}

# Known role categories
ROLE_DICTIONARY = {
    "developer", "engineer", "architect", "programmer", "manager", "lead", "director",
    "designer", "analyst", "administrator", "consultant", "scientist", "specialist",
    "partner", "executive", "recruiter", "coordinator"
}

# Known domain concepts
DOMAIN_DICTIONARY = {
    "frontend": ["frontend", "front-end", "ui", "ux", "web", "client"],
    "backend": ["backend", "back-end", "server", "api", "systems"],
    "fullstack": ["fullstack", "full-stack", "full stack"],
    "data": ["data", "machine learning", "ml", "ai", "analytics"],
    "devops": ["devops", "sre", "infrastructure", "cloud", "platform"],
    "product": ["product", "pm"],
    "design": ["design", "product design", "ux", "ui"],
    "management": ["manager", "management", "director", "head", "lead"],
    "admin": ["administrative", "admin", "business partner", "office"],
    "sales": ["sales", "account manager", "account executive", "business development"]
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
        Parses raw user query text into a structured SearchContext.
        """
        raw_text = (query or "").strip()
        tokens = [t.lower() for t in re.findall(r'[\w\.\+\#\-]+', raw_text)]

        roles: List[IntentTerm] = []
        technologies: List[IntentTerm] = []
        domains: List[IntentTerm] = []
        seniority: List[IntentTerm] = []
        loc_terms: List[IntentTerm] = []

        q_lower = raw_text.lower()

        # 1. Identify Technologies
        for tech in TECH_DICTIONARY:
            if tech in q_lower:
                technologies.append(IntentTerm(name=tech, confidence=1.0))

        # 2. Identify Roles
        for role in ROLE_DICTIONARY:
            if role in tokens:
                roles.append(IntentTerm(name=role, confidence=1.0))

        # 3. Identify Domains
        for domain, keywords in DOMAIN_DICTIONARY.items():
            if any(kw in q_lower for kw in keywords):
                domains.append(IntentTerm(name=domain, confidence=1.0))

        # 4. Identify Seniority
        for sen in SENIORITY_DICTIONARY:
            if sen in tokens:
                seniority.append(IntentTerm(name=sen, confidence=1.0))

        # 5. Location
        if location:
            loc_terms.append(IntentTerm(name=location.strip(), confidence=1.0))
        if remote_only or "remote" in q_lower:
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
