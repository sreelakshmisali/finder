"""
DuckDuckGo Search Provider

Implements `SearchProvider` using DuckDuckGo Web API / HTTP endpoint.
Exposes `is_available` set to True by default (no mandatory API key required).
"""

import os
import logging
from typing import List, Optional
import httpx

from app.providers.search_engine.base_search import SearchProvider, SearchResult

logger = logging.getLogger(__name__)


class DuckDuckGoSearchProvider(SearchProvider):
    """
    Search provider plugin for DuckDuckGo Web Search.
    """

    def __init__(self, enabled: bool = True):
        self._enabled = enabled

    @property
    def name(self) -> str:
        return "duckduckgo"

    @property
    def display_name(self) -> str:
        return "DuckDuckGo Search"

    @property
    def is_available(self) -> bool:
        return self._enabled

    async def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Executes DuckDuckGo Web Search API query.
        """
        if not self.is_available:
            return []

        results: List[SearchResult] = []
        url = "https://html.duckduckgo.com/html/"
        data = {"q": query}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Finder/1.0"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, data=data, headers=headers)
                if resp.status_code == 200:
                    import re
                    pattern = r'<a[^>]+class=["\']result__url["\'][^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
                    matches = re.findall(pattern, resp.text, re.IGNORECASE)
                    for raw_url, raw_title in matches[:limit]:
                        clean_url = raw_url.strip()
                        clean_title = re.sub(r'<[^>]+>', '', raw_title).strip()
                        if clean_url.startswith("//"):
                            clean_url = "https:" + clean_url
                        results.append(
                            SearchResult(
                                title=clean_title or "Job Result",
                                url=clean_url,
                                snippet=f"Discovered via DuckDuckGo: {clean_title}",
                                engine=self.name
                            )
                        )
        except Exception as exc:
            logger.warning(f"DuckDuckGo Search Provider error: {exc}")

        return results
