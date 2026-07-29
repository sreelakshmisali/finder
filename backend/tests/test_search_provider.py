"""
Unit & Integration Tests for Search Provider & Extractors.
"""

import asyncio
import sys
import os
from typing import List, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.providers.search_engine.base_search import SearchProvider, SearchResult
from app.providers.search_engine.search_discovery import SearchDiscoveryProvider
from app.providers.search_engine.extractors.json_ld import JsonLdExtractor
from app.providers.search_engine.extractors.open_graph import OpenGraphExtractor
from app.providers.search_engine.extractors.meta_tag import MetaTagExtractor
from app.providers.search_engine.extractors.heuristic import HeuristicExtractor
from app.providers.search_engine.extractor_pipeline import JobPageExtractor
from app.providers.base_discovery import DiscoveryContext, ProviderType
from app.providers.registry import registry
from app.schemas.job import JobSearchQuery, NormalizedJob
from app.schemas.tagged_url import TaggedURL
from app.core.scheduler_config import SchedulerConfig


class MockSearchEnginePlugin(SearchProvider):
    def __init__(self, name: str, results: List[SearchResult]):
        self._name = name
        self.results = results

    @property
    def name(self) -> str:
        return self._name

    @property
    def display_name(self) -> str:
        return f"Mock {self._name}"

    @property
    def is_available(self) -> bool:
        return True

    async def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        return self.results


def test_json_ld_extractor():
    html = """
    <html>
    <head>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org/",
          "@type": "JobPosting",
          "title": "Senior Python Engineer",
          "description": "We are hiring a Senior Python Engineer to build scalable APIs.",
          "hiringOrganization": {
            "@type": "Organization",
            "name": "Acme Corp"
          },
          "jobLocation": {
            "@type": "Place",
            "address": {
              "@type": "PostalAddress",
              "addressLocality": "San Francisco",
              "addressRegion": "CA"
            }
          }
        }
        </script>
    </head>
    </html>
    """
    job = asyncio.run(JsonLdExtractor().extract("https://acme.com/jobs/1", html))
    assert job is not None
    assert job.title == "Senior Python Engineer"
    assert job.company == "Acme Corp"
    assert job.location == "San Francisco"
    assert "scalable APIs" in job.description


def test_open_graph_extractor():
    html = """
    <html>
    <head>
        <meta property="og:title" content="Lead React Developer at Stripe" />
        <meta property="og:description" content="Join Stripe as a Lead React Developer working on global payments." />
        <meta property="og:site_name" content="Stripe Careers" />
    </head>
    </html>
    """
    job = asyncio.run(OpenGraphExtractor().extract("https://stripe.com/jobs/2", html))
    assert job is not None
    assert job.title == "Lead React Developer at Stripe"
    assert job.company == "Stripe Careers"
    assert "global payments" in job.description


def test_meta_tag_extractor():
    html = """
    <html>
    <head>
        <title>Backend Engineer (Remote) - Figma</title>
        <meta name="description" content="Figma is seeking a Backend Engineer to build real-time collaboration engine." />
    </head>
    </html>
    """
    job = asyncio.run(MetaTagExtractor().extract("https://figma.com/jobs/3", html))
    assert job is not None
    assert "Backend Engineer" in job.title
    assert "real-time collaboration" in job.description


def test_extractor_pipeline_fallback():
    html = """
    <html>
    <head>
        <title>FastAPI Architect | Cloudflare</title>
        <meta name="description" content="Cloudflare is hiring a FastAPI Architect." />
    </head>
    </html>
    """
    pipeline = JobPageExtractor()
    search_res = SearchResult(
        title="FastAPI Architect | Cloudflare",
        url="https://cloudflare.com/careers/3",
        snippet="Cloudflare is hiring a FastAPI Architect.",
        engine="google"
    )

    assert asyncio.run(JsonLdExtractor().extract("https://cloudflare.com/careers/3", html)) is None
    assert asyncio.run(OpenGraphExtractor().extract("https://cloudflare.com/careers/3", html)) is None

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

    class MockJobExtractor:
        async def extract_from_url(self, url: str, search_result=None, skip_classification=False):
            return NormalizedJob(
                title=f"Mock title for {url}", 
                company=f"Company {url}", 
                location="Rem", 
                description="Desc", 
                url=url, 
                source="mock"
            )

    class MockScheduler:
        config = SchedulerConfig()
        async def schedule(self, candidate_urls, global_dedup=None, target_role="", candidate_results=None):
            unique_urls = list(dict.fromkeys(candidate_urls))
            return [TaggedURL(url=u, provider="mock", priority_score=100) for u in unique_urls]

    discovery = SearchDiscoveryProvider(search_providers=[p1, p2], job_extractor=MockJobExtractor(), scheduler=MockScheduler())
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
