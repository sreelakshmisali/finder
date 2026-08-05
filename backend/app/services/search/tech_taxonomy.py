"""
Technology Taxonomy Data Dictionary

Defines canonical technology mappings and domain classifications.
Pure data module decoupled from extraction and ranking logic.
"""

from typing import Dict, Set

# Mapping of technology names to their associated domain sets
TECH_TO_DOMAINS: Dict[str, Set[str]] = {
    "react": {"frontend"},
    "react.js": {"frontend"},
    "reactjs": {"frontend"},
    "next.js": {"frontend"},
    "nextjs": {"frontend"},
    "vue": {"frontend"},
    "vue.js": {"frontend"},
    "angular": {"frontend"},
    "angularjs": {"frontend"},
    "typescript": {"frontend", "backend"},
    "javascript": {"frontend", "backend"},
    "tailwind": {"frontend"},

    "react_native": {"mobile"},
    "react native": {"mobile"},
    "android": {"mobile"},
    "ios": {"mobile"},
    "swift": {"mobile"},
    "kotlin": {"mobile"},
    "flutter": {"mobile"},

    "unity": {"game"},
    "unreal": {"game"},
    "godot": {"game"},
    "three.js": {"game", "frontend"},
    "game": {"game"},

    "python": {"backend", "data"},
    "django": {"backend"},
    "fastapi": {"backend"},
    "node": {"backend"},
    "node.js": {"backend"},
    "nodejs": {"backend"},
    "java": {"backend"},
    "spring": {"backend"},
    "go": {"backend"},
    "golang": {"backend"},
    "ruby": {"backend"},
    "rails": {"backend"},
    "rust": {"backend"},
    "c#": {"backend", "game"},
    "c++": {"backend", "game"},

    "data": {"data"},
    "machine learning": {"data"},
    "ml": {"data"},
    "ai": {"data"},
    "pytorch": {"data"},
    "tensorflow": {"data"},
    "sql": {"data", "backend"},
    "postgresql": {"data", "backend"},

    "docker": {"devops"},
    "kubernetes": {"devops"},
    "terraform": {"devops"},
    "aws": {"devops"},
    "devops": {"devops"},
    "sre": {"devops"},
}

# Domain keyword triggers in job titles
DOMAIN_TITLE_TRIGGERS: Dict[str, Set[str]] = {
    "frontend": {"frontend", "front-end", "ui", "ux", "web"},
    "backend": {"backend", "back-end", "server", "api", "systems"},
    "fullstack": {"fullstack", "full-stack", "full stack"},
    "game": {"game", "gaming", "unity", "unreal", "graphics"},
    "mobile": {"mobile", "android", "ios"},
    "data": {"data", "machine learning", "ml", "ai", "analytics"},
    "devops": {"devops", "sre", "infrastructure", "cloud"},
    "product": {"product", "pm"},
    "design": {"design", "product design"},
    "admin": {"administrative", "admin", "business partner", "office"},
    "sales": {"sales", "account manager", "account executive", "business development"}
}

# Generic software engineering role titles
GENERIC_ROLES = {"developer", "engineer", "software engineer", "programmer", "architect"}


def get_domains_for_tech(tech: str) -> Set[str]:
    """Returns domain set associated with a technology term."""
    return TECH_TO_DOMAINS.get(tech.lower(), set())
