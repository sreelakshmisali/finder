"""
Search Engine Job Discovery Provider

Unified `JobDiscoveryProvider` orchestrating web search engine plugins (Google, Bing)
and page extraction pipeline. Registered directly in ProviderRegistry.
"""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime

from app.providers.base_discovery import SearchEngineProvider, DiscoveryContext
from app.providers.search_engine.base_search import SearchProvider, SearchResult
from app.providers.search_engine.google_search import GoogleSearchProvider
from app.providers.search_engine.bing_search import BingSearchProvider
from app.providers.search_engine.extractor_pipeline import JobPageExtractor
from app.schemas.job import NormalizedJob

logger = logging.getLogger(__name__)


class SearchDiscoveryProvider(SearchEngineProvider):
    """
    Unified Discovery Provider for Search Engine job discovery.
    """

    def __init__(
        self,
        search_providers: Optional[List[SearchProvider]] = None,
        extractor: Optional[JobPageExtractor] = None
    ):
        self.search_providers = search_providers if search_providers is not None else [
            GoogleSearchProvider(),
            BingSearchProvider()
        ]
        self.extractor = extractor or JobPageExtractor()

    @property
    def source_name(self) -> str:
        return "search_engine"

    @property
    def display_name(self) -> str:
        return "Search Engine Discovery"

    @property
    def description(self) -> str:
        return "Discovers tech job postings across the web via Google & Bing Search engine providers."

    async def discover(self, context: DiscoveryContext) -> List[NormalizedJob]:
        """
        Orchestrates search provider discovery, URL deduplication, and page extraction.
        """
        query_text = context.query.query or "Software Engineer"
        limit = context.query.limit

        # 1. Filter available search providers
        active_providers = [p for p in self.search_providers if p.is_available]
        if not active_providers:
            logger.info("No search engine providers currently configured/available.")
            return []

        # 2. Concurrently execute search across available engines
        search_tasks = [p.search(query=query_text, limit=limit) for p in active_providers]
        search_results_nested = await asyncio.gather(*search_tasks, return_exceptions=True)

        # 3. Aggregate & Deduplicate URLs
        all_results: List[SearchResult] = []
        seen_urls = set()

        for res in search_results_nested:
            if isinstance(res, list):
                for item in res:
                    clean_url = item.url.strip().lower()
                    if clean_url and clean_url not in seen_urls:
                        seen_urls.add(clean_url)
                        all_results.append(item)

        if not all_results:
            return []

        # 4. Extract pages concurrently
        extraction_tasks = [
            self.extractor.extract_job(search_result=item, fetch_page=True)
            for item in all_results[:limit]
        ]
        extracted_jobs = await asyncio.gather(*extraction_tasks, return_exceptions=True)

        normalized_jobs: List[NormalizedJob] = []
        for job in extracted_jobs:
            if isinstance(job, NormalizedJob):
                normalized_jobs.append(job)

        return normalized_jobs

    async def get_details(self, url: str) -> Optional[NormalizedJob]:
        """
        Fetch details for a single web job URL using JobPageExtractor.
        """
        dummy_result = SearchResult(title="Job Listing", url=url, snippet="", engine="direct")
        return await self.extractor.extract_job(dummy_result, fetch_page=True)
