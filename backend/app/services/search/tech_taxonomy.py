"""
Technology Taxonomy Data Module

Provides pure taxonomy data mapping technologies to canonical terms and domain sets.
Independent of extraction logic or ranking code.
"""

from typing import Dict, Set

# Pure taxonomy mapping technologies to canonical names and domain sets
TECH_TO_DOMAINS: Dict[str, Set[str]] = {
    # Frontend
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
    "css": {"frontend"},
    "html": {"frontend"},

    # Mobile
    "react_native": {"mobile"},
    "react native": {"mobile"},
    "reactnative": {"mobile"},
    "android": {"mobile"},
    "ios": {"mobile"},
    "swift": {"mobile"},
    "kotlin": {"mobile"},
    "flutter": {"mobile"},

    # Game
    "unity": {"game"},
    "unreal": {"game"},
    "godot": {"game"},
    "three.js": {"game", "frontend"},
    "game": {"game"},
    "graphics": {"game"},

    # Backend
    "python": {"backend", "data"},
    "django": {"backend"},
    "fastapi": {"backend"},
    "flask": {"backend"},
    "node": {"backend"},
    "node.js": {"backend"},
    "nodejs": {"backend"},
    "java": {"backend"},
    "spring": {"backend"},
    "go": {"backend"},
    "golang": {"backend"},
    "ruby": {"backend"},
    "rails": {"backend"},
    "c#": {"backend", "game"},
    ".net": {"backend"},
    "rust": {"backend"},
    "c++": {"backend", "game"},

    # Data / AI
    "sql": {"data"},
    "postgresql": {"data"},
    "postgres": {"data"},
    "mongodb": {"data"},
    "pytorch": {"data"},
    "tensorflow": {"data"},
    "data": {"data"},
    "ai": {"data"},
    "ml": {"data"},

    # DevOps
    "docker": {"devops"},
    "kubernetes": {"devops"},
    "k8s": {"devops"},
    "terraform": {"devops"},
    "aws": {"devops"},
    "devops": {"devops"},
    "sre": {"devops"}
}

# Generic software engineering role titles
GENERIC_ROLES: Set[str] = {
    "software engineer", "engineer", "developer", "programmer",
    "software developer", "full stack engineer", "fullstack engineer",
    "full stack developer", "fullstack developer", "member of technical staff"
}

# Domain keyword lookup
DOMAIN_KEYWORDS: Dict[str, Set[str]] = {
    "frontend": {"frontend", "front-end", "ui", "ux", "web", "client", "react", "vue", "angular"},
    "backend": {"backend", "back-end", "server", "api", "systems", "python", "node", "java", "go", "ruby"},
    "mobile": {"mobile", "android", "ios", "swift", "kotlin", "flutter", "react_native"},
    "game": {"game", "gaming", "unity", "unreal", "graphics", "3d", "godot"},
    "data": {"data", "machine learning", "ml", "ai", "analytics", "scientist", "pytorch", "tensorflow"},
    "devops": {"devops", "sre", "infrastructure", "cloud", "platform", "kubernetes"},
    "admin": {"administrative", "admin", "business partner", "office", "executive assistant"},
    "sales": {"sales", "account manager", "account executive", "business development"},
    "hr": {"hr", "recruiter", "talent", "human resources"}
}


def get_domains_for_tech(tech_name: str) -> Set[str]:
    """Returns domain set for a given technology name."""
    clean = tech_name.lower().strip()
    return TECH_TO_DOMAINS.get(clean, set())
