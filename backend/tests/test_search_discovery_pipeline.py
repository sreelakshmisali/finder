"""
Integration test for the Search Discovery Pipeline.

Verifies end-to-end execution flow:
Mock Search Provider -> SearchAggregator -> CrawlScheduler -> PageTypeClassifier -> JobExtractor -> NormalizedJob list.
Runs deterministically offline without live network dependencies.
"""

import asyncio
from typing import List

from app.providers.search_engine.base_search import SearchProvider, SearchResult
from app.providers.search_engine.search_discovery import SearchDiscoveryProvider
from app.services.search_aggregator import SearchAggregator
from app.services.crawl.crawl_scheduler import CrawlScheduler
from app.services.job_extractor import JobExtractor
from app.services.extraction.page_fetcher import SmartPageFetcher
from app.providers.base_discovery import DiscoveryContext
from app.schemas.job import JobSearchQuery, NormalizedJob


class MockSearchProvider(SearchProvider):
    """Mock search provider returning candidate job board and posting URLs."""
    def __init__(self, results: List[SearchResult]):
        self._results = results

    @property
    def name(self) -> str:
        return "mock_ddg"

    @property
    def display_name(self) -> str:
        return "Mock DuckDuckGo"

    @property
    def is_available(self) -> bool:
        return True

    async def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        return self._results[:limit]


class MockPageFetcher(SmartPageFetcher):
    """Mock page fetcher returning synthetic HTML for candidate URLs."""
    async def fetch(self, url: str) -> str:
        if "boards.greenhouse.io" in url and "/jobs/101" not in url:
            return """
            <html>
            <head><title>Careers at Acme</title></head>
            <body>
              <a href="https://boards.greenhouse.io/acme/jobs/101">React Developer</a>
            </body>
            </html>
            """
        elif "/jobs/101" in url:
            return """
            <html>
            <head>
              <script type="application/ld+json">
              {
                "@context": "https://schema.org/",
                "@type": "JobPosting",
                "title": "React Developer",
                "description": "We are looking for a Senior React Developer in Kerala.",
                "hiringOrganization": {
                  "@type": "Organization",
                  "name": "Acme Inc"
                },
                "jobLocation": {
                  "@type": "Place",
                  "address": {
                    "@type": "PostalAddress",
                    "addressLocality": "Kerala"
                  }
                }
              }
              </script>
            </head>
            <body>
              <h1>React Developer</h1>
              <a href="https://boards.greenhouse.io/acme/jobs/101#apply">Apply Now</a>
            </body>
            </html>
            """
        return ""


def test_search_discovery_pipeline_integration():
    """
    Integration test verifying the search discovery pipeline:
    SearchAggregator -> CrawlScheduler -> PageTypeClassifier -> JobExtractor -> NormalizedJob
    """
    mock_results = [
        SearchResult(
            title="Acme Careers - React Developer",
            url="https://boards.greenhouse.io/acme",
            snippet="React Developer openings at Acme Inc in Kerala",
            engine="mock_ddg"
        )
    ]

    mock_provider = MockSearchProvider(mock_results)
    aggregator = SearchAggregator(search_providers=[mock_provider])
    fetcher = MockPageFetcher()
    job_extractor = JobExtractor(fetcher=fetcher)

    scheduler = CrawlScheduler()
    # Inject mock fetcher into scheduler
    async def mock_scheduler_fetch(url: str):
        return await fetcher.fetch(url)
    scheduler._fetch = mock_scheduler_fetch

    provider = SearchDiscoveryProvider(
        aggregator=aggregator,
        job_extractor=job_extractor,
        scheduler=scheduler
    )

    ctx = DiscoveryContext(
        query=JobSearchQuery(query="React Developer", location="Kerala", limit=5)
    )

    jobs = asyncio.run(provider.discover(ctx))

    assert len(jobs) >= 1
    job = jobs[0]
    assert isinstance(job, NormalizedJob)
    assert "React Developer" in job.title
    assert job.company.lower() in ["acme inc", "acme"]
    assert job.apply_url is not None


if __name__ == "__main__":
    test_search_discovery_pipeline_integration()
