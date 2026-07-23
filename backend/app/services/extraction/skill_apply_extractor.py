"""
Skill & Apply Link Extractor

Parses required technical skills and resolves direct application form links (`apply_url`)
from career page HTML. Handles relative and absolute Apply URLs.
"""

import re
import logging
from urllib.parse import urljoin, urlparse
from typing import List, Optional, Tuple, Dict, Any

from app.services.tech_mappings import (
    PROGRAMMING_LANGUAGES,
    FRAMEWORKS,
    DATABASES
)

logger = logging.getLogger(__name__)

# Known tech keywords pool
ALL_KNOWN_TECH = PROGRAMMING_LANGUAGES | FRAMEWORKS | DATABASES | {
    "aws", "azure", "gcp", "docker", "kubernetes", "k8s", "terraform", "git",
    "rest", "api", "graphql", "grpc", "ci/cd", "linux", "sql", "nosql", "microservices"
}

# Display name map for technologies
TECH_DISPLAY_NAMES: Dict[str, str] = {
    "fastapi": "FastAPI",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "graphql": "GraphQL",
    "grpc": "gRPC",
    "mongodb": "MongoDB",
    "next.js": "Next.js",
    "react": "React",
    "vue": "Vue",
    "django": "Django",
    "python": "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "aws": "AWS",
    "gcp": "GCP",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "terraform": "Terraform"
}


class SkillAndApplyExtractor:
    """
    Extractor for required technical skills and application URLs.
    """

    @classmethod
    def extract_skills_and_apply_url(
        cls,
        page_url: str,
        html: str,
        description: str = ""
    ) -> Tuple[List[str], Optional[str]]:
        """
        Extracts required skills and absolute Apply URL.

        Args:
            page_url: Original page URL (used to resolve relative links).
            html: Raw HTML content string.
            description: Extracted job description text.

        Returns:
            Tuple of (required_skills: List[str], apply_url: Optional[str])
        """
        skills = cls.extract_skills(html, description)
        apply_url = cls.extract_apply_url(page_url, html)
        return skills, apply_url

    @classmethod
    def extract_skills(cls, html: str, description: str = "") -> List[str]:
        combined_text = (html + " " + description).lower()
        found_skills: List[str] = []

        for tech in ALL_KNOWN_TECH:
            pattern = r'\b' + re.escape(tech) + r'\b'
            if re.search(pattern, combined_text):
                formatted = TECH_DISPLAY_NAMES.get(tech.lower(), tech.title())
                if formatted not in found_skills:
                    found_skills.append(formatted)

        return found_skills[:10]

    @classmethod
    def extract_apply_url(cls, base_url: str, html: str) -> Optional[str]:
        if not html:
            return base_url

        apply_patterns = [
            r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(?:.*?)apply(?:.*?)</a\s*>',
            r'<a[^>]+href=["\']([^"\']+)["\'][^>]*class=["\'][^"\']*apply[^"\']*["\']',
            r'<a[^>]+class=["\'][^"\']*apply[^"\']*["\'][^>]+href=["\']([^"\']+)["\']'
        ]

        for pattern in apply_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            for raw_href in matches:
                href = raw_href.strip()
                if href and not href.startswith("javascript:") and not href.startswith("#"):
                    resolved_url = urljoin(base_url, href)
                    return resolved_url

        return base_url
