"""
Technology Tag Extractor for Companies

Extracts tech stack tags (languages, frameworks, databases, cloud tools) from company descriptions.
"""

import re
from typing import List
from app.services.tech_mappings import PROGRAMMING_LANGUAGES, FRAMEWORKS, DATABASES

TECH_POOL = PROGRAMMING_LANGUAGES | FRAMEWORKS | DATABASES | {
    "aws", "gcp", "azure", "docker", "kubernetes", "k8s", "terraform", "graphql", "rest", "grpc"
}

TECH_DISPLAY_NAMES = {
    "fastapi": "FastAPI",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "python": "Python",
    "django": "Django",
    "react": "React",
    "vue": "Vue",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "graphql": "GraphQL",
    "grpc": "gRPC",
    "aws": "AWS",
    "gcp": "GCP",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "terraform": "Terraform"
}


class TechTagExtractor:
    """
    Extracts tech stack keywords from company text.
    """

    @classmethod
    def extract_tags(cls, text: str, max_tags: int = 8) -> List[str]:
        if not text:
            return []

        clean_text = text.lower()
        tags: List[str] = []

        for tech in TECH_POOL:
            pattern = r'\b' + re.escape(tech) + r'\b'
            if re.search(pattern, clean_text):
                formatted = TECH_DISPLAY_NAMES.get(tech.lower(), tech.capitalize())
                if formatted not in tags:
                    tags.append(formatted)

        return tags[:max_tags]
