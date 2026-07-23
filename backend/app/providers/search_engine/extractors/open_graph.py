"""
OpenGraph Meta Tag Extractor

Parses `og:title`, `og:site_name`, `og:description` meta tags from page HTML.
"""

import re
import logging
from typing import Optional, Dict
from datetime import datetime

from app.providers.search_engine.base_search import SearchResult
from app.providers.search_engine.extractors.base_extractor import BaseExtractor
from app.schemas.job import NormalizedJob

logger = logging.getLogger(__name__)


class OpenGraphExtractor(BaseExtractor):
    """
    Extractor for OpenGraph meta tags.
    """

    @property
    def name(self) -> str:
        return "open_graph"

    async def extract(
        self,
        url: str,
        html: str,
        search_result: Optional[SearchResult] = None
    ) -> Optional[NormalizedJob]:
        if not html:
            return None

        og_data: Dict[str, str] = {}
        pattern = r'<meta\s+property=["\']og:([a-zA-Z0-9_:.]+)["\']\s+content=["\']([^"\']+)["\']'
        matches = re.findall(pattern, html, re.IGNORECASE)

        for prop, content in matches:
            og_data[prop.lower()] = content.strip()

        # Check reverse attribute ordering <meta content="..." property="og:...">
        rev_pattern = r'<meta\s+content=["\']([^"\']+)["\']\s+property=["\']og:([a-zA-Z0-9_:.]+)["\']'
        rev_matches = re.findall(rev_pattern, html, re.IGNORECASE)
        for content, prop in rev_matches:
            og_data[prop.lower()] = content.strip()

        title = og_data.get("title") or (search_result.title if search_result else None)
        if not title:
            return None

        site_name = og_data.get("site_name") or "Company"
        description = og_data.get("description") or (search_result.snippet if search_result else f"{title} position.")

        is_remote = "remote" in title.lower() or "remote" in description.lower()

        return NormalizedJob(
            company=site_name,
            title=title,
            location="Remote" if is_remote else "Onsite / Hybrid",
            remote=is_remote,
            salary=None,
            description=description,
            url=url,
            source="search_engine",
            posted_date=datetime.utcnow()
        )
