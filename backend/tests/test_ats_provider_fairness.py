"""
ATS Provider Company-Fairness Tests

Verifies that Greenhouse, Lever, and Ashby distribute discovery quota fairly
across all companies in their hardcoded lists, so one busy company cannot
starve others before global ranking.

Starvation scenario (old behaviour, now a regression):
  - query.limit = 50
  - First company has 100 jobs
  - Old code: fills all 50 slots from first company, loop breaks, rest never visited
  - New code: first company gets at most ceil(limit/n_companies) slots, all companies visited

Tests three queries from the audit: React Developer, Python Developer, Django Developer.
"""

import math
import re
import asyncio
from collections import Counter
from unittest.mock import patch
import pytest

from app.providers.greenhouse import GreenhouseProvider, SAMPLE_BOARDS as GREENHOUSE_BOARDS
from app.providers.lever import LeverProvider, SAMPLE_LEVER_COMPANIES
from app.providers.ashby import AshbyProvider, SAMPLE_ASHBY_COMPANIES
from app.providers.base_discovery import DiscoveryContext
from app.schemas.job import JobSearchQuery


# ─── Fake HTTP helpers ────────────────────────────────────────────────────────

class _FakeResponse:
    """Minimal httpx.Response stand-in."""
    def __init__(self, data):
        self.status_code = 200
        self._data = data

    def json(self):
        return self._data


def _gh_body(board: str, n: int, keyword: str) -> dict:
    return {
        "jobs": [
            {
                "title": f"{keyword} Engineer {i}",
                "location": {"name": "Remote"},
                "absolute_url": f"https://boards.greenhouse.io/{board}/jobs/{i}",
                "content": f"{keyword} role at {board} — job {i}",
            }
            for i in range(n)
        ]
    }


def _lever_body(company: str, n: int, keyword: str) -> list:
    return [
        {
            "text": f"{keyword} Developer {i}",
            "categories": {"location": "Remote"},
            "hostedUrl": f"https://jobs.lever.co/{company}/{i}",
            "descriptionPlain": f"{keyword} at {company} job {i}",
            "workplaceType": "remote",
        }
        for i in range(n)
    ]


def _ashby_body(board: str, n: int, keyword: str) -> dict:
    return {
        "jobs": [
            {
                "title": f"{keyword} Specialist {i}",
                "locationName": "Remote",
                "jobUrl": f"https://jobs.ashbyhq.com/{board}/{i}",
                "isRemote": True,
            }
            for i in range(n)
        ]
    }


# ─── Mock async HTTP clients ─────────────────────────────────────────────────

class _FakeGHClient:
    """Mocks httpx.AsyncClient for Greenhouse (boards-api.greenhouse.io)."""

    def __init__(self, n_jobs: int, keyword: str):
        self._n = n_jobs
        self._kw = keyword

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def get(self, url, **kwargs):
        m = re.search(r"/boards/(\w+)/jobs", url)
        board = m.group(1) if m else "unknown"
        return _FakeResponse(_gh_body(board, self._n, self._kw))


class _FakeLeverClient:
    """Mocks httpx.AsyncClient for Lever (api.lever.co)."""

    def __init__(self, n_jobs: int, keyword: str):
        self._n = n_jobs
        self._kw = keyword

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def get(self, url, **kwargs):
        m = re.search(r"/postings/(\w+)", url)
        company = m.group(1) if m else "unknown"
        return _FakeResponse(_lever_body(company, self._n, self._kw))


class _FakeAshbyClient:
    """Mocks httpx.AsyncClient for Ashby (api.ashbyhq.com)."""

    def __init__(self, n_jobs: int, keyword: str):
        self._n = n_jobs
        self._kw = keyword

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def get(self, url, **kwargs):
        m = re.search(r"/job-board/(\w+)", url)
        board = m.group(1) if m else "unknown"
        return _FakeResponse(_ashby_body(board, self._n, self._kw))


# ─── Greenhouse ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("keyword", ["React Developer", "Python Developer", "Django Developer"])
async def test_greenhouse_all_companies_contribute(keyword):
    """With 10 jobs per company, every company in the list must appear in results."""
    provider = GreenhouseProvider()
    query = JobSearchQuery(query=keyword, limit=50)
    ctx = DiscoveryContext(query=query)

    with patch("app.providers.greenhouse.httpx.AsyncClient",
               return_value=_FakeGHClient(10, keyword)):
        results = await provider.discover(ctx)

    assert len(results) <= 50
    companies = {r.company for r in results}
    expected = {b.capitalize() for b in GREENHOUSE_BOARDS}
    assert companies == expected, (
        f"[{keyword}] Missing companies: {expected - companies}"
    )


@pytest.mark.asyncio
async def test_greenhouse_per_company_cap_enforced():
    """No company may exceed ceil(limit / n_companies) candidates."""
    provider = GreenhouseProvider()
    query = JobSearchQuery(query="React Developer", limit=50)
    ctx = DiscoveryContext(query=query)
    cap = max(5, math.ceil(50 / len(GREENHOUSE_BOARDS)))

    with patch("app.providers.greenhouse.httpx.AsyncClient",
               return_value=_FakeGHClient(100, "React Developer")):
        results = await provider.discover(ctx)

    counts = Counter(r.company for r in results)
    for company, count in counts.items():
        assert count <= cap, (
            f"Greenhouse company '{company}' returned {count} > cap {cap}"
        )


@pytest.mark.asyncio
async def test_greenhouse_starvation_regression():
    """Regression: first company must NOT be able to consume all 50 slots."""
    provider = GreenhouseProvider()
    query = JobSearchQuery(query="React Developer", limit=50)
    ctx = DiscoveryContext(query=query)
    first = GREENHOUSE_BOARDS[0].capitalize()

    with patch("app.providers.greenhouse.httpx.AsyncClient",
               return_value=_FakeGHClient(100, "React Developer")):
        results = await provider.discover(ctx)

    first_count = sum(1 for r in results if r.company == first)
    assert first_count < 50, (
        f"Starvation detected: '{first}' holds {first_count}/50 slots — "
        "outer break not removed"
    )


@pytest.mark.asyncio
async def test_greenhouse_sparse_companies_still_work():
    """If each company has fewer jobs than the cap, we still get all of them."""
    provider = GreenhouseProvider()
    query = JobSearchQuery(query="React Developer", limit=50)
    ctx = DiscoveryContext(query=query)

    with patch("app.providers.greenhouse.httpx.AsyncClient",
               return_value=_FakeGHClient(2, "React Developer")):
        results = await provider.discover(ctx)

    # 2 jobs × 10 companies = 20 total; every company still represented
    assert len(results) == 2 * len(GREENHOUSE_BOARDS)
    companies = {r.company for r in results}
    assert companies == {b.capitalize() for b in GREENHOUSE_BOARDS}


@pytest.mark.asyncio
async def test_greenhouse_global_limit_respected():
    """Total results never exceed query.limit even with many companies."""
    provider = GreenhouseProvider()
    query = JobSearchQuery(query="Python Developer", limit=30)
    ctx = DiscoveryContext(query=query)

    with patch("app.providers.greenhouse.httpx.AsyncClient",
               return_value=_FakeGHClient(100, "Python Developer")):
        results = await provider.discover(ctx)

    assert len(results) <= 30


# ─── Lever ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("keyword", ["React Developer", "Python Developer", "Django Developer"])
async def test_lever_all_companies_contribute(keyword):
    """With 10 jobs per company, every Lever company must appear in results."""
    provider = LeverProvider()
    query = JobSearchQuery(query=keyword, limit=50)
    ctx = DiscoveryContext(query=query)

    with patch("app.providers.lever.httpx.AsyncClient",
               return_value=_FakeLeverClient(10, keyword)):
        results = await provider.discover(ctx)

    assert len(results) <= 50
    companies = {r.company for r in results}
    expected = {c.capitalize() for c in SAMPLE_LEVER_COMPANIES}
    assert companies == expected, (
        f"[{keyword}] Missing companies: {expected - companies}"
    )


@pytest.mark.asyncio
async def test_lever_per_company_cap_enforced():
    """No Lever company may exceed its per-company cap."""
    provider = LeverProvider()
    query = JobSearchQuery(query="Python Developer", limit=50)
    ctx = DiscoveryContext(query=query)
    cap = max(5, math.ceil(50 / len(SAMPLE_LEVER_COMPANIES)))

    with patch("app.providers.lever.httpx.AsyncClient",
               return_value=_FakeLeverClient(100, "Python Developer")):
        results = await provider.discover(ctx)

    counts = Counter(r.company for r in results)
    for company, count in counts.items():
        assert count <= cap, (
            f"Lever company '{company}' returned {count} > cap {cap}"
        )


@pytest.mark.asyncio
async def test_lever_starvation_regression():
    """Regression: first Lever company must NOT consume all 50 slots."""
    provider = LeverProvider()
    query = JobSearchQuery(query="Python Developer", limit=50)
    ctx = DiscoveryContext(query=query)
    first = SAMPLE_LEVER_COMPANIES[0].capitalize()

    with patch("app.providers.lever.httpx.AsyncClient",
               return_value=_FakeLeverClient(100, "Python Developer")):
        results = await provider.discover(ctx)

    first_count = sum(1 for r in results if r.company == first)
    assert first_count < 50, (
        f"Starvation detected: '{first}' holds {first_count}/50 slots"
    )


@pytest.mark.asyncio
async def test_lever_global_limit_respected():
    provider = LeverProvider()
    query = JobSearchQuery(query="Django Developer", limit=20)
    ctx = DiscoveryContext(query=query)

    with patch("app.providers.lever.httpx.AsyncClient",
               return_value=_FakeLeverClient(100, "Django Developer")):
        results = await provider.discover(ctx)

    assert len(results) <= 20


# ─── Ashby ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("keyword", ["React Developer", "Python Developer", "Django Developer"])
async def test_ashby_all_companies_contribute(keyword):
    """With 10 jobs per company, every Ashby company must appear in results."""
    provider = AshbyProvider()
    query = JobSearchQuery(query=keyword, limit=50)
    ctx = DiscoveryContext(query=query)

    with patch("app.providers.ashby.httpx.AsyncClient",
               return_value=_FakeAshbyClient(10, keyword)):
        results = await provider.discover(ctx)

    assert len(results) <= 50
    companies = {r.company for r in results}
    expected = {b.capitalize() for b in SAMPLE_ASHBY_COMPANIES}
    assert companies == expected, (
        f"[{keyword}] Missing companies: {expected - companies}"
    )


@pytest.mark.asyncio
async def test_ashby_per_company_cap_enforced():
    """No Ashby company may exceed its per-company cap."""
    provider = AshbyProvider()
    query = JobSearchQuery(query="Django Developer", limit=50)
    ctx = DiscoveryContext(query=query)
    cap = max(5, math.ceil(50 / len(SAMPLE_ASHBY_COMPANIES)))

    with patch("app.providers.ashby.httpx.AsyncClient",
               return_value=_FakeAshbyClient(100, "Django Developer")):
        results = await provider.discover(ctx)

    counts = Counter(r.company for r in results)
    for company, count in counts.items():
        assert count <= cap, (
            f"Ashby company '{company}' returned {count} > cap {cap}"
        )


@pytest.mark.asyncio
async def test_ashby_starvation_regression():
    """Regression: first Ashby company must NOT consume all 50 slots."""
    provider = AshbyProvider()
    query = JobSearchQuery(query="Django Developer", limit=50)
    ctx = DiscoveryContext(query=query)
    first = SAMPLE_ASHBY_COMPANIES[0].capitalize()

    with patch("app.providers.ashby.httpx.AsyncClient",
               return_value=_FakeAshbyClient(100, "Django Developer")):
        results = await provider.discover(ctx)

    first_count = sum(1 for r in results if r.company == first)
    assert first_count < 50, (
        f"Starvation detected: '{first}' holds {first_count}/50 slots"
    )


@pytest.mark.asyncio
async def test_ashby_global_limit_respected():
    provider = AshbyProvider()
    query = JobSearchQuery(query="React Developer", limit=15)
    ctx = DiscoveryContext(query=query)

    with patch("app.providers.ashby.httpx.AsyncClient",
               return_value=_FakeAshbyClient(100, "React Developer")):
        results = await provider.discover(ctx)

    assert len(results) <= 15


# ─── Cross-provider: cap formula scales with limit ───────────────────────────

@pytest.mark.asyncio
async def test_cap_scales_with_limit():
    """Verify cap formula: max(5, ceil(limit/n)) adjusts with different limit values."""
    provider = GreenhouseProvider()
    n = len(GREENHOUSE_BOARDS)  # 10

    for limit, expected_cap in [(10, 5), (50, 5), (100, 10), (200, 20)]:
        query = JobSearchQuery(query="React Developer", limit=limit)
        ctx = DiscoveryContext(query=query)

        with patch("app.providers.greenhouse.httpx.AsyncClient",
                   return_value=_FakeGHClient(100, "React Developer")):
            results = await provider.discover(ctx)

        assert len(results) <= limit, f"limit={limit}: got {len(results)} > {limit}"
        counts = Counter(r.company for r in results)
        for company, count in counts.items():
            assert count <= expected_cap, (
                f"limit={limit}: '{company}' has {count} > expected_cap {expected_cap}"
            )
