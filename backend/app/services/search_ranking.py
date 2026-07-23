"""
Search Result Ranker Service

Decoupled ranking engine scoring multi-engine search results based on engine consensus,
provider weights, keyword density, and snippet relevance.
"""

import re
import logging
from typing import List, Dict, Any, Optional

from app.providers.search_engine.base_search import SearchResult

logger = logging.getLogger(__name__)

# Configurable provider weight factors
DEFAULT_PROVIDER_WEIGHTS: Dict[str, float] = {
    "google": 1.0,
    "bing": 0.9,
    "brave": 0.8,
    "duckduckgo": 0.8,
    "fallback": 0.5
}


class SearchResultRanker:
    """
    Ranks merged SearchResult items based on multi-engine consensus and keyword relevance.
    """

    def __init__(self, provider_weights: Optional[Dict[str, float]] = None):
        self.provider_weights = provider_weights or DEFAULT_PROVIDER_WEIGHTS

    def rank_results(
        self,
        results: List[SearchResult],
        query: str
    ) -> List[SearchResult]:
        """
        Ranks search results in priority descending order.

        Args:
            results: List of merged SearchResult objects with `metadata['discovered_by']`.
            query: Target search query string.

        Returns:
            Ranked list of `SearchResult` objects.
        """
        if not results:
            return []

        query_tokens = set(re.findall(r'\w+', query.lower()))

        def compute_score(item: SearchResult) -> float:
            score = 50.0

            # 1. Multi-engine consensus boost (+25 pts per additional discovery engine)
            discovered_by = item.metadata.get("discovered_by", [item.engine])
            score += (len(discovered_by) - 1) * 25.0

            # 2. Provider weight factor
            primary_engine = item.engine.lower()
            weight = self.provider_weights.get(primary_engine, 0.7)
            score *= weight

            # 3. Keyword density boost (+5 pts per matching token in title/snippet)
            combined_text = (item.title + " " + item.snippet).lower()
            for token in query_tokens:
                if len(token) > 2 and token in combined_text:
                    score += 5.0

            # 4. ATS domain boost (+15 pts for direct Greenhouse/Lever/Ashby URLs)
            if any(ats in item.url.lower() for ats in ["greenhouse.io", "lever.co", "ashbyhq.com"]):
                score += 15.0

            return score

        # Sort by computed score descending, maintaining stable title order for ties
        ranked = sorted(results, key=lambda item: (-compute_score(item), item.title))
        return ranked
