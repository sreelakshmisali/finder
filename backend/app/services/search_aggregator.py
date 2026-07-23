"""
Search Aggregator Service

Executes parallel searches across provider-agnostic `SearchProvider` plugins with isolated timeouts,
normalizes target URLs, tracks multi-engine discovery metadata, and ranks results via `SearchResultRanker`.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Set, Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from app.providers.search_engine.base_search import SearchProvider, SearchResult
from app.providers.search_engine.google_search import GoogleSearchProvider
from app.providers.search_engine.bing_search import BingSearchProvider
from app.providers.search_engine.brave_search import BraveSearchProvider
from app.providers.search_engine.duckduckgo_search import DuckDuckGoSearchProvider
from app.services.search_ranking import SearchResultRanker

logger = logging.getLogger(__name__)

# List of common tracking parameters to strip during URL normalization
TRACKING_PARAMS: Set[str] = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "fbclid", "gclid", "msclkid", "_ga"
}


class SearchAggregator:
    """
    Provider-agnostic aggregator for executing, merging, deduplicating, and ranking multi-engine search results.
    """

    def __init__(
        self,
        search_providers: Optional[List[SearchProvider]] = None,
        ranker: Optional[SearchResultRanker] = None,
        provider_timeout: float = 10.0
    ):
        self.search_providers = search_providers if search_providers is not None else [
            GoogleSearchProvider(),
            BingSearchProvider(),
            BraveSearchProvider(),
            DuckDuckGoSearchProvider()
        ]
        self.ranker = ranker or SearchResultRanker()
        self.provider_timeout = provider_timeout

    async def aggregate_search(
        self,
        query: str,
        limit: int = 20
    ) -> List[SearchResult]:
        """
        Executes parallel search across all available providers, normalizes URLs,
        deduplicates entries, tracks discovered sources, and ranks results.

        Args:
            query: Target search query string.
            limit: Maximum number of ranked results to return.

        Returns:
            List of deduplicated, source-tracked, ranked `SearchResult` objects.
        """
        active_providers = [p for p in self.search_providers if p.is_available]
        if not active_providers:
            logger.info("No active search providers available for search aggregation.")
            return []

        # Concurrently execute searches with isolated provider timeouts
        async def run_single_provider(provider: SearchProvider) -> List[SearchResult]:
            try:
                return await asyncio.wait_for(
                    provider.search(query=query, limit=limit),
                    timeout=self.provider_timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Search provider '{provider.name}' timed out after {self.provider_timeout}s.")
                return []
            except Exception as exc:
                logger.warning(f"Search provider '{provider.name}' failed with error: {exc}")
                return []

        tasks = [run_single_provider(p) for p in active_providers]
        results_nested = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge, normalize URLs, and track discovered sources
        merged_map: Dict[str, SearchResult] = {}

        for res_list in results_nested:
            if isinstance(res_list, list):
                for item in res_list:
                    norm_url = self.normalize_url(item.url)
                    if not norm_url:
                        continue

                    if norm_url not in merged_map:
                        # Initialize metadata with discovered_by list
                        item.url = norm_url
                        item.metadata = item.metadata or {}
                        item.metadata["discovered_by"] = [item.engine]
                        merged_map[norm_url] = item
                    else:
                        # Append provider engine to discovered_by list if new
                        existing = merged_map[norm_url]
                        discovered_by = existing.metadata.get("discovered_by", [existing.engine])
                        if item.engine not in discovered_by:
                            discovered_by.append(item.engine)
                        existing.metadata["discovered_by"] = discovered_by

        merged_results = list(merged_map.values())
        if not merged_results:
            return []

        # Rank search results
        ranked_results = self.ranker.rank_results(results=merged_results, query=query)
        return ranked_results[:limit]

    @classmethod
    def normalize_url(cls, raw_url: str) -> str:
        """
        Robust URL normalization:
        - Lowercase scheme & netloc
        - Strip trailing slashes
        - Remove fragments (#...)
        - Remove tracking query parameters (utm_*, ref, fbclid)
        - Canonicalize query parameter order
        """
        if not raw_url or not isinstance(raw_url, str):
            return ""

        url_str = raw_url.strip()
        if url_str.startswith("//"):
            url_str = "https:" + url_str

        parsed = urlparse(url_str)
        if not parsed.scheme or not parsed.netloc:
            return raw_url.strip()

        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()

        # Remove default port
        if scheme == "http" and netloc.endswith(":80"):
            netloc = netloc[:-3]
        elif scheme == "https" and netloc.endswith(":443"):
            netloc = netloc[:-4]

        # Strip trailing slash from path
        path = parsed.path.rstrip("/") if parsed.path != "/" else "/"

        # Strip tracking query parameters & sort remaining params
        query_dict = parse_qs(parsed.query, keep_blank_values=False)
        clean_query = {
            k: v for k, v in query_dict.items()
            if k.lower() not in TRACKING_PARAMS
        }

        # Canonicalize query string
        sorted_query = urlencode(sorted((k, v) for k, v_list in clean_query.items() for v in v_list))

        # Reconstruct clean URL without fragment
        clean_url = urlunparse((scheme, netloc, path, parsed.params, sorted_query, ""))
        return clean_url
