"""
Google Search Provider

Implements `SearchProvider` using official Google Custom Search JSON API.
Exposes `is_available` based on API key configuration.
"""

import os
import logging
from typing import List, Optional
import httpx

from app.providers.search_engine.base_search import SearchProvider, SearchResult

logger = logging.getLogger(__name__)


class GoogleSearchProvider(SearchProvider):
    """
    Search provider plugin for Google Custom Search JSON API.
    """

    def __init__(self, api_key: Optional[str] = None, cx: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_SEARCH_API_KEY", "")
        self.cx = cx or os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")

    @property
    def name(self) -> str:
        return "google"

    @property
    def display_name(self) -> str:
        return "Google Search"

    @property
    def is_available(self) -> bool:
        return bool(self.api_key and self.cx)

    async def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Executes Google Custom Search API query.
        """
        if not self.is_available:
            logger.warning("GoogleSearchProvider called but is_available is False (missing API credentials).")
            return []

        results: List[SearchResult] = []
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": min(limit, 10)
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code != 200:
                    logger.error(f"Google Search API returned status code {resp.status_code}: {resp.text}")
                    return []

                data = resp.json()
                items = data.get("items", [])
                for item in items:
                    results.append(
                        SearchResult(
                            title=item.get("title", ""),
                            url=item.get("link", ""),
                            snippet=item.get("snippet", ""),
                            engine=self.name,
                            metadata={"pagemap": item.get("pagemap", {})}
                        )
                    )
        except Exception as exc:
            logger.error(f"Google Search Provider error: {exc}")

        return results
