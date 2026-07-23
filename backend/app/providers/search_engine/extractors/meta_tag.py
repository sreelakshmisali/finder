"""
Meta Tag & Page Title Extractor

Parses standard HTML `<title>`, `<meta name="description">`, and `<meta name="author">` tags.
"""

import re
import logging
from typing import Optional
from datetime import datetime

from app.providers.search_engine.base_search import SearchResult
from app.providers.search_engine.extractors.base_extractor import BaseExtractor
from app.schemas.job import NormalizedJob

logger = logging.getLogger(__name__)


class MetaTagExtractor(BaseExtractor):
    """
    Extractor for standard HTML title and meta tags.
    """

    @property
    def name(self) -> str:
        return "meta_tag"

    async def extract(
        self,
        url: str,
        html: str,
        search_result: Optional[SearchResult] = None
    ) -> Optional[NormalizedJob]:
        if not html:
            return None

        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        raw_title = title_match.group(1).strip() if title_match else ""

        desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        description = desc_match.group(1).strip() if desc_match else ""

        if not raw_title and search_result:
            raw_title = search_result.title
        if not description and search_result:
            description = search_result.snippet

        if not raw_title:
            return None

        # Infer company from title splitting e.g. "Software Engineer - Stripe Careers"
        company = "Company"
        clean_title = raw_title
        if " - " in raw_title:
            parts = raw_title.split(" - ")
            clean_title = parts[0].strip()
            company = parts[-1].replace("Careers", "").replace("Jobs", "").strip() or "Company"
        elif " | " in raw_title:
            parts = raw_title.split(" | ")
            clean_title = parts[0].strip()
            company = parts[-1].replace("Careers", "").replace("Jobs", "").strip() or "Company"

        is_remote = "remote" in clean_title.lower() or "remote" in description.lower()

        return NormalizedJob(
            company=company,
            title=clean_title,
            location="Remote" if is_remote else "Onsite / Hybrid",
            remote=is_remote,
            salary=None,
            description=description or f"{clean_title} position.",
            url=url,
            source="search_engine",
            posted_date=datetime.utcnow()
        )
