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
        url = "https://lite.duckduckgo.com/lite/"
        data = {"q": query}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Finder/1.0"
        }


        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, data=data, headers=headers)
                if resp.status_code == 200:
                    import re
                    matches = []
                    for m in re.finditer(r'<a[^>]+href=[\'"]([^\'"]+)[\'"][^>]+class=[\'"]result-link[\'"][^>]*>(.*?)</a>', resp.text, re.IGNORECASE):
                        matches.append((m.group(1), m.group(2)))
                    for m in re.finditer(r'<a[^>]+class=[\'"]result-link[\'"][^>]+href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', resp.text, re.IGNORECASE):
                        matches.append((m.group(1), m.group(2)))
                    
                    
                    all_urls = []
                    for m in matches:
                        u = m[0].strip()
                        if u.startswith("//"):
                            u = "https:" + u
                        all_urls.append(u)

                    from app.utils.pipeline_tracker import current_tracker
                    tracker = current_tracker.get()
                    if tracker:
                        tracker.record_discovery(query, self.name, all_urls)

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
            from app.utils.pipeline_tracker import current_tracker
            tracker = current_tracker.get()
            if tracker:
                tracker._add_event("search_provider_failed", {"engine": self.name, "query": query, "error": str(exc)})
            logger.warning(f"DuckDuckGo Search Provider error: {exc}")

        return results
