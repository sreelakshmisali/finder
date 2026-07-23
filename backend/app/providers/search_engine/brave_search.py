"""
Brave Search Provider

Implements `SearchProvider` using official Brave Search API.
Exposes `is_available` based on API key configuration.
"""

import os
import logging
from typing import List, Optional
import httpx

from app.providers.search_engine.base_search import SearchProvider, SearchResult

logger = logging.getLogger(__name__)


class BraveSearchProvider(SearchProvider):
    """
    Search provider plugin for Brave Search Web API.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("BRAVE_SEARCH_API_KEY", "")

    @property
    def name(self) -> str:
        return "brave"

    @property
    def display_name(self) -> str:
        return "Brave Search"

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    async def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Executes Brave Search API query.
        """
        if not self.is_available:
            logger.warning("BraveSearchProvider called but is_available is False (missing API credential).")
            return []

        results: List[SearchResult] = []
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key
        }
        params = {"q": query, "count": limit}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code != 200:
                    logger.error(f"Brave Search API returned status code {resp.status_code}: {resp.text}")
                    return []

                data = resp.json()
                web_results = data.get("web", {}).get("results", [])
                for item in web_results:
                    results.append(
                        SearchResult(
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            snippet=item.get("description", ""),
                            engine=self.name
                        )
                    )
        except Exception as exc:
            logger.error(f"Brave Search Provider error: {exc}")

        return results
