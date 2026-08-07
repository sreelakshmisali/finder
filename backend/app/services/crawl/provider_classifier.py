"""
Provider Classifier

Classifies URLs into provider category tags and extracts company name heuristics.
"""

import re
from urllib.parse import urlparse
from typing import List, Tuple, Optional, Any


class ProviderClassifier:
    """Classifies provider category tags and extracts company heuristics."""

    DOMAIN_PATTERNS: List[Tuple[re.Pattern, str]] = [
        (re.compile(r"boards(\.[a-z]+)?\.greenhouse\.io", re.I), "greenhouse"),
        (re.compile(r"jobs\.lever\.co", re.I), "lever"),
        (re.compile(r"jobs\.ashbyhq\.com", re.I), "ashby"),
        (re.compile(r"\.myworkdayjobs\.com", re.I), "workday"),
        (re.compile(r"jobs\.smartrecruiters\.com", re.I), "smartrecruiters"),
        (re.compile(r"jobs\.jobvite\.com", re.I), "jobvite"),
        (re.compile(r"\.bamboohr\.com", re.I), "bamboohr"),
        (re.compile(r"apply\.workable\.com", re.I), "workable"),
        (re.compile(r"linkedin\.com", re.I), "linkedin"),
        (re.compile(r"infopark\.in", re.I), "infopark"),
        (re.compile(r"technopark\.", re.I), "technopark"),
    ]

    CAREER_PATH_SIGNALS = ["/careers", "/jobs", "/openings", "/positions", "/work-with-us"]

    @classmethod
    def classify(cls, url: str) -> str:
        """Returns provider tag. Unknown domains default to generic_board."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()

        for pattern, tag in cls.DOMAIN_PATTERNS:
            if pattern.search(domain):
                return tag

        if any(sig in path for sig in cls.CAREER_PATH_SIGNALS):
            return "company_career"

        return "generic_board"

    @classmethod
    def extract_company_name(cls, url: str, search_result: Optional[Any] = None) -> Optional[str]:
        """
        Extracts company name heuristic from ATS URL path or SearchResult title/snippet.
        Used to populate TaggedURL.company for global company cap enforcement.
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.strip("/")

        # 1. ATS domain URL path extraction
        if "greenhouse.io" in domain:
            parts = path.split("/")
            if parts and parts[0] != "embed":
                return parts[0].capitalize()
        elif "lever.co" in domain:
            parts = path.split("/")
            if parts:
                return parts[0].capitalize()
        elif "ashbyhq.com" in domain:
            parts = path.split("/")
            if parts:
                return parts[0].capitalize()
        elif "myworkdayjobs.com" in domain:
            subdomain = domain.split(".")[0]
            return subdomain.capitalize()

        # 2. SearchResult title/snippet parsing fallback (e.g. "Software Engineer at Stripe")
        if search_result and hasattr(search_result, "title"):
            title = getattr(search_result, "title", "")
            match = re.search(r"\bat\s+([A-Z][A-Za-z0-9\s&]{2,20})\b", title)
            if match:
                return match.group(1).strip()

        return None
