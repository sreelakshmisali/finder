"""
Unit & Integration Tests for Multi Search Engine Aggregators (Task 17)

Tests SearchAggregator, SearchResultRanker, URL tracking parameter normalization,
discovered source metadata tracking, multi-engine consensus scoring, and failure isolation.
"""

import asyncio
from app.providers.search_engine.base_search import SearchProvider, SearchResult
from app.providers.search_engine.brave_search import BraveSearchProvider
from app.providers.search_engine.duckduckgo_search import DuckDuckGoSearchProvider
from app.services.search_ranking import SearchResultRanker
from app.services.search_aggregator import SearchAggregator


class MockEnginePlugin(SearchProvider):
    """
    Mock Search Engine Plugin for testing multi-engine search aggregation.
    """
    def __init__(self, name: str, results: list, delay: float = 0.0, should_fail: bool = False):
        self._name = name
        self._results = results
        self.delay = delay
        self.should_fail = should_fail

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
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        if self.should_fail:
            raise RuntimeError(f"Engine {self._name} simulated crash")
        return self._results[:limit]


def test_url_normalization():
    """
    Test URL normalization stripping tracking parameters, fragments, and trailing slashes.
    """
    raw = "HTTPS://WWW.EXAMPLE.COM/jobs/backend/?utm_source=google&ref=123#apply-now"
    normalized = SearchAggregator.normalize_url(raw)

    assert normalized == "https://www.example.com/jobs/backend"


def test_search_aggregator_multi_engine_merge_and_metadata():
    """
    Test parallel search aggregation, URL deduplication, and discovered_by metadata tracking.
    """
    duplicate_url = "https://greenhouse.io/stripe/jobs/101?utm_source=search"
    res_google = [
        SearchResult(title="Stripe Python Engineer", url=duplicate_url, snippet="Python backend role", engine="google"),
        SearchResult(title="Figma Lead Dev", url="https://lever.co/figma/jobs/202", snippet="Figma role", engine="google")
    ]
    res_bing = [
        SearchResult(title="Stripe Python Engineer", url="https://greenhouse.io/stripe/jobs/101", snippet="Python backend role", engine="bing")
    ]
    res_brave = [
        SearchResult(title="Stripe Python Engineer", url="https://greenhouse.io/stripe/jobs/101#section", snippet="Python backend role", engine="brave")
    ]

    p1 = MockEnginePlugin("google", res_google)
    p2 = MockEnginePlugin("bing", res_bing)
    p3 = MockEnginePlugin("brave", res_brave)

    aggregator = SearchAggregator(search_providers=[p1, p2, p3])
    ranked = asyncio.run(aggregator.aggregate_search("Python Engineer", limit=10))

    # All 3 engines returned the same Stripe URL variation -> merged into 1 item
    assert len(ranked) == 2
    stripe_item = next(r for r in ranked if "stripe" in r.url)

    # Verify discovered_by metadata preserves all 3 discovering engines
    discovered_by = stripe_item.metadata.get("discovered_by", [])
    assert "google" in discovered_by
    assert "bing" in discovered_by
    assert "brave" in discovered_by


def test_search_result_ranker_consensus_boost():
    """
    Test that SearchResultRanker ranks URLs discovered by multiple engines higher.
    """
    item_single = SearchResult(
        title="Single Engine Job",
        url="https://company.com/job/1",
        snippet="Software Engineer",
        engine="google",
        metadata={"discovered_by": ["google"]}
    )

    item_consensus = SearchResult(
        title="Consensus Job",
        url="https://company.com/job/2",
        snippet="Software Engineer",
        engine="google",
        metadata={"discovered_by": ["google", "bing", "brave"]}
    )

    ranker = SearchResultRanker()
    ranked = ranker.rank_results([item_single, item_consensus], query="Software Engineer")

    # Item with consensus from 3 engines ranks first
    assert ranked[0].url == "https://company.com/job/2"


def test_failure_isolation_and_timeouts():
    """
    Test that SearchAggregator handles failing or timing out providers gracefully without failing search.
    """
    res_good = [SearchResult(title="Good Job", url="https://good.com/job", snippet="Good", engine="good_engine")]

    good_p = MockEnginePlugin("good_engine", res_good)
    failing_p = MockEnginePlugin("failing_engine", [], should_fail=True)
    timing_out_p = MockEnginePlugin("slow_engine", res_good, delay=5.0)

    aggregator = SearchAggregator(
        search_providers=[good_p, failing_p, timing_out_p],
        provider_timeout=0.2
    )

    results = asyncio.run(aggregator.aggregate_search("Job", limit=10))
    assert len(results) == 1
    assert results[0].url == "https://good.com/job"


if __name__ == "__main__":
    test_url_normalization()
    test_search_aggregator_multi_engine_merge_and_metadata()
    test_search_result_ranker_consensus_boost()
    test_failure_isolation_and_timeouts()
    print("ALL 4 SEARCH AGGREGATOR TESTS PASSED SUCCESSFULLY!")
