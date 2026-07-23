"""
Bing Search Provider

Implements `SearchProvider` using official Bing Web Search API v7.
Exposes `is_available` based on API key configuration.
"""

import os
import logging
from typing import List, Optional
import httpx

from app.providers.search_engine.base_search import SearchProvider, SearchResult

logger = logging.getLogger(__name__)


class BingSearchProvider(SearchProvider):
    """
    Search provider plugin for Bing Web Search API.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("BING_SEARCH_API_KEY", "")

    @property
    def name(self) -> str:
        return "bing"

    @property
    def display_name(self) -> str:
        return "Bing Search"

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    async def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Executes Bing Web Search API query.
        """
        if not self.is_available:
            logger.warning("BingSearchProvider called but is_available is False (missing API credential).")
            return []

        results: List[SearchResult] = []
        endpoint = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        params = {"q": query, "count": limit}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(endpoint, headers=headers, params=params)
                if resp.status_code != 200:
                    logger.error(f"Bing Search API returned status code {resp.status_code}: {resp.text}")
                    return []

                data = resp.json()
                web_pages = data.get("webPages", {}).get("value", [])
                for page in web_pages:
                    results.append(
                        SearchResult(
                            title=page.get("name", ""),
                            url=page.get("url", ""),
                            snippet=page.get("snippet", ""),
                            engine=self.name
                        )
                    )
        except Exception as exc:
            logger.error(f"Bing Search Provider error: {exc}")

        return results
