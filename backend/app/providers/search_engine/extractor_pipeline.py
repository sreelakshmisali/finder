"""
Pluggable Job Page Extractor Pipeline

Executes specialized extractors in prioritized sequence:
[JSON-LD -> OpenGraph -> Meta Tags -> Heuristic Fallback]
"""

import logging
from typing import List, Optional
import httpx

from app.providers.search_engine.base_search import SearchResult
from app.providers.search_engine.extractors.base_extractor import BaseExtractor
from app.providers.search_engine.extractors.json_ld import JsonLdExtractor
from app.providers.search_engine.extractors.open_graph import OpenGraphExtractor
from app.providers.search_engine.extractors.meta_tag import MetaTagExtractor
from app.providers.search_engine.extractors.heuristic import HeuristicExtractor
from app.schemas.job import NormalizedJob

logger = logging.getLogger(__name__)


class JobPageExtractor:
    """
    Orchestrates page fetching and multi-tier extractor fallback chain.
    """

    def __init__(self, extractors: Optional[List[BaseExtractor]] = None):
        self.extractors = extractors or [
            JsonLdExtractor(),
            OpenGraphExtractor(),
            MetaTagExtractor(),
            HeuristicExtractor()
        ]

    async def fetch_html(self, url: str, timeout: float = 8.0) -> str:
        """
        Fetches web page HTML content with timeouts and error handling.
        """
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Finder/1.0 Job Discovery Engine"}
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    return resp.text
        except Exception as exc:
            logger.debug(f"Failed to fetch HTML for '{url}': {exc}")
        return ""

    async def extract_job(
        self,
        search_result: SearchResult,
        fetch_page: bool = True
    ) -> Optional[NormalizedJob]:
        """
        Attempts extraction by running each extractor in sequence until one returns a NormalizedJob.
        """
        url = search_result.url
        html = ""

        if fetch_page:
            html = await self.fetch_html(url)

        for extractor in self.extractors:
            try:
                job = await extractor.extract(url=url, html=html, search_result=search_result)
                if job:
                    logger.debug(f"Extractor '{extractor.name}' succeeded for URL: {url}")
                    return job
            except Exception as exc:
                logger.warning(f"Extractor '{extractor.name}' raised error for '{url}': {exc}")

        return None
