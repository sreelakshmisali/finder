"""
Unit & Integration Tests for Search Engine Based Job Discovery

Tests SearchProvider interface, Google & Bing providers, pluggable JobPageExtractor pipeline,
URL deduplication, fallback chain order, and SearchDiscoveryProvider registry integration.
"""

import asyncio
from app.providers.search_engine.base_search import SearchProvider, SearchResult
from app.providers.search_engine.google_search import GoogleSearchProvider
from app.providers.search_engine.bing_search import BingSearchProvider
from app.providers.search_engine.extractors.json_ld import JsonLdExtractor
from app.providers.search_engine.extractors.open_graph import OpenGraphExtractor
from app.providers.search_engine.extractors.meta_tag import MetaTagExtractor
from app.providers.search_engine.extractors.heuristic import HeuristicExtractor
from app.providers.search_engine.extractor_pipeline import JobPageExtractor
from app.providers.search_engine.search_discovery import SearchDiscoveryProvider
from app.providers.registry import registry, ProviderType
from app.schemas.job import JobSearchQuery, NormalizedJob
from app.providers.base_discovery import DiscoveryContext


class MockSearchEnginePlugin(SearchProvider):
    """
    Controlled Mock Search Engine for testing provider discovery and URL deduplication.
    """
    def __init__(self, name: str, results: list):
        self._name = name
        self._results = results

    @property
    def name(self) -> str:
        return self._name

    @property
    def display_name(self) -> str:
        return f"Mock {self._name.capitalize()}"

    @property
    def is_available(self) -> bool:
        return True

    async def search(self, query: str, limit: int = 10) -> list:
        return self._results[:limit]


def test_search_provider_availability():
    """
    Verify Google and Bing search providers report is_available correctly without API keys.
    """
    google = GoogleSearchProvider(api_key="", cx="")
    bing = BingSearchProvider(api_key="")

    assert google.is_available is False
    assert bing.is_available is False


def test_json_ld_extractor():
    """
    Test extraction of Schema.org JobPosting JSON-LD.
    """
    html = '''
    <html>
      <head>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org/",
          "@type": "JobPosting",
          "title": "Backend Software Engineer",
          "hiringOrganization": {
            "@type": "Organization",
            "name": "Acme Corp"
          },
          "jobLocation": {
            "@type": "Place",
            "address": {
              "addressLocality": "San Francisco"
            }
          },
          "description": "Building high performance microservices."
        }
        </script>
      </head>
    </html>
    '''
    extractor = JsonLdExtractor()
    job = asyncio.run(extractor.extract("https://acme.com/jobs/1", html))

    assert job is not None
    assert job.title == "Backend Software Engineer"
    assert job.company == "Acme Corp"
    assert job.location == "San Francisco"
    assert "microservices" in job.description


def test_open_graph_extractor():
    """
    Test extraction of OpenGraph meta tags.
    """
    html = '''
    <html>
      <head>
        <meta property="og:title" content="Senior Python Developer (Remote)" />
        <meta property="og:site_name" content="Stripe" />
        <meta property="og:description" content="Join our core payment infrastructure team." />
      </head>
    </html>
    '''
    extractor = OpenGraphExtractor()
    job = asyncio.run(extractor.extract("https://stripe.com/jobs/2", html))

    assert job is not None
    assert job.title == "Senior Python Developer (Remote)"
    assert job.company == "Stripe"
    assert job.remote is True


def test_extractor_pipeline_fallback():
    """
    Test that JobPageExtractor falls back through extractors cleanly when earlier extractors fail.
    """
    # Plain HTML without JSON-LD or OpenGraph tags
    html = '''
    <html>
      <head>
        <title>FastAPI Architect | Cloudflare Careers</title>
        <meta name="description" content="Lead API design for edge network." />
      </head>
    </html>
    '''
    search_res = SearchResult(
        title="FastAPI Architect - Cloudflare",
        url="https://cloudflare.com/careers/3",
        snippet="Lead API design for edge network.",
        engine="mock"
    )

    pipeline = JobPageExtractor()
    # Test JsonLd returns None
    assert asyncio.run(JsonLdExtractor().extract("https://cloudflare.com/careers/3", html)) is None
    # Test OpenGraph returns None
    assert asyncio.run(OpenGraphExtractor().extract("https://cloudflare.com/careers/3", html)) is None

    # Pipeline falls through to MetaTagExtractor
    job = asyncio.run(pipeline.extract_job(search_res, fetch_page=False))
    assert job is not None
    assert "FastAPI Architect" in job.title


def test_search_discovery_url_deduplication():
    """
    Test that SearchDiscoveryProvider deduplicates duplicate URLs across search providers.
    """
    duplicate_url = "https://greenhouse.io/jobs/100"
    res1 = [
        SearchResult(title="Python Dev", url=duplicate_url, snippet="Desc 1", engine="g1"),
        SearchResult(title="Django Dev", url="https://lever.co/jobs/200", snippet="Desc 2", engine="g1")
    ]
    res2 = [
        SearchResult(title="Python Dev Dup", url=duplicate_url, snippet="Desc 1", engine="b1")
    ]

    p1 = MockSearchEnginePlugin("g1", res1)
    p2 = MockSearchEnginePlugin("b1", res2)

    discovery = SearchDiscoveryProvider(search_providers=[p1, p2])
    ctx = DiscoveryContext(query=JobSearchQuery(query="Python", limit=10))

    jobs = asyncio.run(discovery.discover(ctx))
    assert len(jobs) == 2  # duplicate_url deduplicated from 3 items to 2


def test_provider_registry_search_engine_integration():
    """
    Verify that SearchDiscoveryProvider is properly registered in ProviderRegistry.
    """
    search_providers = registry.get_enabled_providers(provider_type=ProviderType.SEARCH_ENGINE)
    assert len(search_providers) >= 1
    assert any(p.source_name == "search_engine" for p in search_providers)


if __name__ == "__main__":
    test_search_provider_availability()
    test_json_ld_extractor()
    test_open_graph_extractor()
    test_extractor_pipeline_fallback()
    test_search_discovery_url_deduplication()
    test_provider_registry_search_engine_integration()
    print("ALL 6 SEARCH PROVIDER TESTS PASSED SUCCESSFULLY!")
