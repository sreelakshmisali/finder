"""
JSON-LD Schema.org JobPosting Extractor

Extracts structured job posting fields from embedded <script type="application/ld+json"> blocks.
"""

import json
import re
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.providers.search_engine.base_search import SearchResult
from app.providers.search_engine.extractors.base_extractor import BaseExtractor
from app.schemas.job import NormalizedJob

logger = logging.getLogger(__name__)


class JsonLdExtractor(BaseExtractor):
    """
    Extractor for Schema.org JobPosting JSON-LD metadata.
    """

    @property
    def name(self) -> str:
        return "json_ld"

    async def extract(
        self,
        url: str,
        html: str,
        search_result: Optional[SearchResult] = None
    ) -> Optional[NormalizedJob]:
        if not html:
            return None

        # Find all JSON-LD script blocks
        pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)

        for content in matches:
            try:
                data = json.loads(content.strip())

                # Handle top-level object or @graph list
                items = data if isinstance(data, list) else [data]
                if isinstance(data, dict) and "@graph" in data:
                    items = data["@graph"]

                for item in items:
                    if isinstance(item, dict) and item.get("@type") == "JobPosting":
                        return self._parse_job_posting(item, url, search_result)

            except (json.JSONDecodeError, TypeError) as exc:
                logger.debug(f"JSON-LD parse error: {exc}")
                continue

        return None

    def _parse_job_posting(
        self,
        item: Dict[str, Any],
        url: str,
        search_result: Optional[SearchResult]
    ) -> NormalizedJob:
        title = item.get("title") or (search_result.title if search_result else "Software Role")

        # Parse Organization / Company
        hiring_org = item.get("hiringOrganization")
        company = "Technology Company"
        if isinstance(hiring_org, dict):
            company = hiring_org.get("name") or company
        elif isinstance(hiring_org, str):
            company = hiring_org

        # Parse Location & Remote
        job_location = item.get("jobLocation")
        loc_str = "Remote"
        is_remote = False

        if isinstance(job_location, dict):
            address = job_location.get("address")
            if isinstance(address, dict):
                loc_str = address.get("addressLocality") or address.get("addressRegion") or "Remote"
            elif isinstance(address, str):
                loc_str = address

        job_location_type = item.get("jobLocationType", "")
        if "TELECOMMUTE" in str(job_location_type).upper() or "remote" in loc_str.lower() or "remote" in title.lower():
            is_remote = True

        description = item.get("description") or (search_result.snippet if search_result else f"{title} at {company}")

        return NormalizedJob(
            company=company,
            title=title,
            location=loc_str,
            remote=is_remote,
            salary=None,
            description=description,
            url=url,
            source="search_engine",
            posted_date=datetime.utcnow()
        )
