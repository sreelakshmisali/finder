"""
Search Engine Job Discovery Provider

Unified `JobDiscoveryProvider` orchestrating multi search engine aggregation (Google, Bing, Brave, DuckDuckGo)
and career page extraction via `JobExtractor`. Registered directly in ProviderRegistry.
"""

import asyncio
import logging
from typing import List, Optional, Any
from datetime import datetime

from app.providers.base_discovery import SearchEngineProvider, DiscoveryContext
from app.providers.search_engine.base_search import SearchProvider, SearchResult
from app.services.search_aggregator import SearchAggregator
from app.schemas.job import NormalizedJob

logger = logging.getLogger(__name__)


class SearchDiscoveryProvider(SearchEngineProvider):
    """
    Unified Discovery Provider for Multi-Search Engine job discovery.
    """

    def __init__(
        self,
        search_providers: Optional[List[SearchProvider]] = None,
        aggregator: Optional[SearchAggregator] = None,
        job_extractor: Optional[Any] = None
    ):
        if aggregator:
            self.aggregator = aggregator
        elif search_providers:
            self.aggregator = SearchAggregator(search_providers=search_providers)
        else:
            self.aggregator = SearchAggregator()
        self._job_extractor = job_extractor

    @property
    def job_extractor(self):
        if self._job_extractor is None:
            from app.services.job_extractor import JobExtractor
            self._job_extractor = JobExtractor()
        return self._job_extractor

    @property
    def source_name(self) -> str:
        return "search_engine"

    @property
    def display_name(self) -> str:
        return "Search Engine Discovery"

    @property
    def description(self) -> str:
        return "Discovers tech job postings across the web by aggregating Google, Bing, Brave & DuckDuckGo Search engines."

    async def discover(self, context: DiscoveryContext) -> List[NormalizedJob]:
        """
        Orchestrates multi-engine search aggregation, URL deduplication, ranking, and career page extraction.
        """
        query_text = context.query.query or "Software Engineer"
        limit = context.query.limit

        # 1. Aggregate, deduplicate, and rank search results across multi-search engines
        ranked_results = await self.aggregator.aggregate_search(query=query_text, limit=limit)
        if not ranked_results:
            return []

        # 2. Extract career pages concurrently via JobExtractor
        extraction_tasks = [
            self.job_extractor.extract_from_url(url=item.url, search_result=item)
            for item in ranked_results[:limit]
        ]
        extracted_jobs = await asyncio.gather(*extraction_tasks, return_exceptions=True)

        normalized_jobs: List[NormalizedJob] = []
        for job in extracted_jobs:
            if isinstance(job, NormalizedJob):
                normalized_jobs.append(job)

        return normalized_jobs

    async def get_details(self, url: str) -> Optional[NormalizedJob]:
        """
        Fetch details for a single web job URL using JobExtractor.
        """
        return await self.job_extractor.extract_from_url(url=url)
