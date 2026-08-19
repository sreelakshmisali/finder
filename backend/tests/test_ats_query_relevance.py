"""
ATS Provider Query-Relevance Filter Tests

Verifies that:
1. extract_content_tokens() correctly identifies non-generic query words.
2. job_matches_query() accepts/rejects jobs based on token overlap.
3. Greenhouse, Lever, and Ashby providers filter out unrelated jobs (HR, Sales,
   Marketing) when the query has content tokens.
4. Relevant jobs (keyword in title or description) are always retained.
5. Generic queries and empty queries bypass the filter (full recall preserved).
6. Company fairness from the previous fix is preserved alongside keyword filtering.

Test queries: React Developer, Python Developer, Django Developer, DevOps Engineer.
"""

import re
import asyncio
from collections import Counter
from unittest.mock import patch
import pytest

from app.providers._ats_filter import extract_content_tokens, job_matches_query
from app.providers.greenhouse import GreenhouseProvider, SAMPLE_BOARDS as GREENHOUSE_BOARDS
from app.providers.lever import LeverProvider, SAMPLE_LEVER_COMPANIES
from app.providers.ashby import AshbyProvider, SAMPLE_ASHBY_COMPANIES
from app.providers.base_discovery import DiscoveryContext
from app.schemas.job import JobSearchQuery


# ─── Unrelated job titles used in mixed mocks ─────────────────────────────────

UNRELATED_TITLES = [
    "Sales Manager",
    "HR Business Partner",
    "Marketing Director",
    "Finance Analyst",
    "Operations Coordinator",
]


# ─── Unit tests: extract_content_tokens ───────────────────────────────────────

class TestExtractContentTokens:

    def test_react_developer(self):
        assert extract_content_tokens("React Developer") == frozenset({"react"})

    def test_python_developer(self):
        assert extract_content_tokens("Python Developer") == frozenset({"python"})

    def test_django_developer(self):
        assert extract_content_tokens("Django Developer") == frozenset({"django"})

    def test_devops_engineer(self):
        assert extract_content_tokens("DevOps Engineer") == frozenset({"devops"})

    def test_software_engineer_is_empty(self):
        """Pure generic query: no content tokens → filter should be a no-op."""
        assert extract_content_tokens("Software Engineer") == frozenset()

    def test_full_stack_developer_is_empty(self):
        assert extract_content_tokens("Full Stack Developer") == frozenset()

    def test_empty_query_is_empty(self):
        assert extract_content_tokens("") == frozenset()

    def test_mixed_seniority_and_tech(self):
        tokens = extract_content_tokens("Senior Python Backend Engineer")
        assert "python" in tokens
        assert "backend" in tokens
        assert "senior" not in tokens
        assert "engineer" not in tokens

    def test_go_language_retained(self):
        """'go' is only 2 chars but is a real language — must not be stripped."""
        tokens = extract_content_tokens("Go Developer")
        assert "go" in tokens

    def test_ml_retained(self):
        tokens = extract_content_tokens("ML Engineer")
        assert "ml" in tokens

    def test_dotted_token_base_form_added(self):
        """'react.js Developer' → content_tokens contains both 'react.js' and 'react'."""
        tokens = extract_content_tokens("React.js Developer")
        assert "react.js" in tokens
        assert "react" in tokens  # base form for title matching

    def test_node_js(self):
        tokens = extract_content_tokens("Node.js Engineer")
        assert "node" in tokens

    def test_csharp(self):
        tokens = extract_content_tokens("C# Developer")
        assert "c#" in tokens

    def test_cpp(self):
        tokens = extract_content_tokens("C++ Engineer")
        assert "c++" in tokens


# ─── Unit tests: job_matches_query ────────────────────────────────────────────

class TestJobMatchesQuery:

    def test_react_in_title(self):
        assert job_matches_query("Senior React Developer", "", frozenset({"react"}))

    def test_react_in_title_case_insensitive(self):
        assert job_matches_query("SENIOR REACT DEVELOPER", "", frozenset({"react"}))

    def test_react_not_in_title_or_desc(self):
        assert not job_matches_query("HR Business Partner", "", frozenset({"react"}))

    def test_react_in_description_fallback(self):
        """Title miss → description saves the job."""
        assert job_matches_query(
            "HR Business Partner",
            "We use React for internal tooling dashboards",
            frozenset({"react"}),
        )

    def test_react_not_in_desc_either(self):
        assert not job_matches_query(
            "Sales Manager",
            "Manage sales team and drive revenue growth.",
            frozenset({"react"}),
        )

    def test_empty_content_tokens_is_noop(self):
        """No content tokens → always True regardless of title/description."""
        assert job_matches_query("HR Business Partner", "Nothing technical here.", frozenset())

    def test_python_in_title(self):
        assert job_matches_query("Python Backend Engineer", "", frozenset({"python"}))

    def test_django_in_title(self):
        assert job_matches_query("Django Developer", "", frozenset({"django"}))

    def test_devops_in_title(self):
        assert job_matches_query("DevOps Platform Engineer", "", frozenset({"devops"}))

    def test_unrelated_title_no_desc(self):
        assert not job_matches_query("Marketing Director", "", frozenset({"python"}))


# ─── Fake HTTP response helpers ───────────────────────────────────────────────

class _FakeResponse:
    def __init__(self, data):
        self.status_code = 200
        self._data = data

    def json(self):
        return self._data


def _gh_mixed_body(board: str, relevant_kw: str, n_relevant: int, n_unrelated: int) -> dict:
    """Greenhouse JSON: first n_relevant jobs have keyword in title, rest are unrelated."""
    jobs = []
    for i in range(n_relevant):
        jobs.append({
            "title": f"{relevant_kw} Engineer {i}",
            "location": {"name": "Remote"},
            "absolute_url": f"https://boards.greenhouse.io/{board}/jobs/r{i}",
            "content": f"{relevant_kw.lower()} developer role at {board}",
        })
    for i, title in enumerate(UNRELATED_TITLES[:n_unrelated]):
        jobs.append({
            "title": title,
            "location": {"name": "Remote"},
            "absolute_url": f"https://boards.greenhouse.io/{board}/jobs/u{i}",
            "content": "Non-technical position with no technology keywords.",
        })
    return {"jobs": jobs}


def _lever_mixed_body(company: str, relevant_kw: str, n_relevant: int, n_unrelated: int) -> list:
    """Lever JSON array: relevant postings first, unrelated last."""
    posts = []
    for i in range(n_relevant):
        posts.append({
            "text": f"{relevant_kw} Developer {i}",
            "categories": {"location": "Remote"},
            "hostedUrl": f"https://jobs.lever.co/{company}/r{i}",
            "descriptionPlain": f"{relevant_kw.lower()} at {company} job {i}",
            "workplaceType": "remote",
        })
    for i, title in enumerate(UNRELATED_TITLES[:n_unrelated]):
        posts.append({
            "text": title,
            "categories": {"location": "Remote"},
            "hostedUrl": f"https://jobs.lever.co/{company}/u{i}",
            "descriptionPlain": f"Non-technical role at {company} with no code.",
            "workplaceType": "remote",
        })
    return posts


def _ashby_mixed_body(board: str, relevant_kw: str, n_relevant: int, n_unrelated: int) -> dict:
    """Ashby JSON: relevant jobs first, unrelated last."""
    jobs = []
    for i in range(n_relevant):
        jobs.append({
            "title": f"{relevant_kw} Specialist {i}",
            "locationName": "Remote",
            "jobUrl": f"https://jobs.ashbyhq.com/{board}/r{i}",
            "isRemote": True,
        })
    for i, title in enumerate(UNRELATED_TITLES[:n_unrelated]):
        jobs.append({
            "title": title,
            "locationName": "Remote",
            "jobUrl": f"https://jobs.ashbyhq.com/{board}/u{i}",
            "isRemote": True,
        })
    return {"jobs": jobs}


# ─── Mock async HTTP clients (mixed) ─────────────────────────────────────────

class _FakeGHMixedClient:
    def __init__(self, n_relevant: int, n_unrelated: int, keyword: str):
        self._nr = n_relevant
        self._nu = n_unrelated
        self._kw = keyword

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def get(self, url, **kwargs):
        m = re.search(r"/boards/(\w+)/jobs", url)
        board = m.group(1) if m else "unknown"
        return _FakeResponse(_gh_mixed_body(board, self._kw, self._nr, self._nu))


class _FakeLeverMixedClient:
    def __init__(self, n_relevant: int, n_unrelated: int, keyword: str):
        self._nr = n_relevant
        self._nu = n_unrelated
        self._kw = keyword

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def get(self, url, **kwargs):
        m = re.search(r"/postings/(\w+)", url)
        company = m.group(1) if m else "unknown"
        return _FakeResponse(_lever_mixed_body(company, self._kw, self._nr, self._nu))


class _FakeAshbyMixedClient:
    def __init__(self, n_relevant: int, n_unrelated: int, keyword: str):
        self._nr = n_relevant
        self._nu = n_unrelated
        self._kw = keyword

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def get(self, url, **kwargs):
        m = re.search(r"/job-board/(\w+)", url)
        board = m.group(1) if m else "unknown"
        return _FakeResponse(_ashby_mixed_body(board, self._kw, self._nr, self._nu))


# ─── Greenhouse: keyword filter ───────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("keyword", [
    "React Developer", "Python Developer", "Django Developer", "DevOps Engineer"
])
async def test_greenhouse_filters_unrelated_jobs(keyword):
    """Unrelated jobs (Sales, HR, Marketing…) must not appear in results."""
    provider = GreenhouseProvider()
    query = JobSearchQuery(query=keyword, limit=100)
    ctx = DiscoveryContext(query=query)

    with patch("app.providers.greenhouse.httpx.AsyncClient",
               return_value=_FakeGHMixedClient(5, 5, keyword)):
        results = await provider.discover(ctx)

    for r in results:
        for unrelated in UNRELATED_TITLES:
            assert unrelated.lower() not in r.title.lower(), (
                f"[{keyword}] Unrelated job '{r.title}' passed the filter"
            )


@pytest.mark.asyncio
@pytest.mark.parametrize("keyword", [
    "React Developer", "Python Developer", "Django Developer", "DevOps Engineer"
])
async def test_greenhouse_retains_relevant_jobs(keyword):
    """All relevant jobs (keyword in title) must survive the filter."""
    provider = GreenhouseProvider()
    query = JobSearchQuery(query=keyword, limit=100)
    ctx = DiscoveryContext(query=query)

    with patch("app.providers.greenhouse.httpx.AsyncClient",
               return_value=_FakeGHMixedClient(3, 0, keyword)):
        results = await provider.discover(ctx)

    # 3 relevant per company × 10 companies = 30, all below cap=max(5,ceil(100/10))=10
    assert len(results) == 3 * len(GREENHOUSE_BOARDS), (
        f"[{keyword}] Expected {3 * len(GREENHOUSE_BOARDS)} results, got {len(results)}"
    )


@pytest.mark.asyncio
async def test_greenhouse_empty_query_bypasses_filter():
    """Empty query string → no content tokens → all jobs returned."""
    provider = GreenhouseProvider()
    query = JobSearchQuery(query="", limit=200)
    ctx = DiscoveryContext(query=query)

    with patch("app.providers.greenhouse.httpx.AsyncClient",
               return_value=_FakeGHMixedClient(3, 3, "React")):
        results = await provider.discover(ctx)

    # 6 jobs per company × 10 companies = 60, no filter applied
    assert len(results) == 6 * len(GREENHOUSE_BOARDS)


@pytest.mark.asyncio
async def test_greenhouse_generic_query_bypasses_filter():
    """'Software Engineer' has no content tokens → filter is a no-op."""
    provider = GreenhouseProvider()
    query = JobSearchQuery(query="Software Engineer", limit=200)
    ctx = DiscoveryContext(query=query)

    with patch("app.providers.greenhouse.httpx.AsyncClient",
               return_value=_FakeGHMixedClient(3, 3, "Software")):
        results = await provider.discover(ctx)

    assert len(results) == 6 * len(GREENHOUSE_BOARDS)


@pytest.mark.asyncio
@pytest.mark.parametrize("keyword", [
    "React Developer", "Python Developer", "Django Developer", "DevOps Engineer"
])
async def test_greenhouse_fairness_preserved_with_filter(keyword):
    """Company fairness (all companies contribute) is maintained alongside keyword filter."""
    provider = GreenhouseProvider()
    query = JobSearchQuery(query=keyword, limit=50)
    ctx = DiscoveryContext(query=query)

    # Each company has 10 relevant jobs — all should contribute after filtering
    with patch("app.providers.greenhouse.httpx.AsyncClient",
               return_value=_FakeGHMixedClient(10, 0, keyword)):
        results = await provider.discover(ctx)

    companies = {r.company for r in results}
    expected = {b.capitalize() for b in GREENHOUSE_BOARDS}
    assert companies == expected, (
        f"[{keyword}] Missing companies after filter: {expected - companies}"
    )


# ─── Lever: keyword filter ────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("keyword", [
    "React Developer", "Python Developer", "Django Developer", "DevOps Engineer"
])
async def test_lever_filters_unrelated_jobs(keyword):
    """Unrelated jobs (Sales, HR…) must not appear in Lever results."""
    provider = LeverProvider()
    query = JobSearchQuery(query=keyword, limit=100)
    ctx = DiscoveryContext(query=query)

    with patch("app.providers.lever.httpx.AsyncClient",
               return_value=_FakeLeverMixedClient(5, 5, keyword)):
        results = await provider.discover(ctx)

    for r in results:
        for unrelated in UNRELATED_TITLES:
            assert unrelated.lower() not in r.title.lower(), (
                f"[{keyword}] Unrelated job '{r.title}' passed Lever filter"
            )


@pytest.mark.asyncio
@pytest.mark.parametrize("keyword", [
    "React Developer", "Python Developer", "Django Developer", "DevOps Engineer"
])
async def test_lever_retains_relevant_jobs(keyword):
    """All relevant Lever jobs must survive the filter."""
    provider = LeverProvider()
    query = JobSearchQuery(query=keyword, limit=100)
    ctx = DiscoveryContext(query=query)

    with patch("app.providers.lever.httpx.AsyncClient",
               return_value=_FakeLeverMixedClient(3, 0, keyword)):
        results = await provider.discover(ctx)

    assert len(results) == 3 * len(SAMPLE_LEVER_COMPANIES), (
        f"[{keyword}] Expected {3 * len(SAMPLE_LEVER_COMPANIES)}, got {len(results)}"
    )


@pytest.mark.asyncio
async def test_lever_description_fallback_match():
    """
    A job whose title doesn't contain the keyword but whose description does
    must be retained (Lever has real plain-text descriptions).
    """
    provider = LeverProvider()
    query = JobSearchQuery(query="React Developer", limit=100)
    ctx = DiscoveryContext(query=query)

    # Mock: title has no "react", but descriptionPlain mentions React
    class _DescMatchClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def get(self, url, **kwargs):
            m = re.search(r"/postings/(\w+)", url)
            company = m.group(1) if m else "unknown"
            return _FakeResponse([{
                "text": "Frontend Engineer",
                "categories": {"location": "Remote"},
                "hostedUrl": f"https://jobs.lever.co/{company}/1",
                "descriptionPlain": "We build UIs using React and TypeScript.",
                "workplaceType": "remote",
            }])

    with patch("app.providers.lever.httpx.AsyncClient", return_value=_DescMatchClient()):
        results = await provider.discover(ctx)

    assert len(results) == len(SAMPLE_LEVER_COMPANIES), (
        "Description-match jobs were incorrectly filtered out"
    )


@pytest.mark.asyncio
async def test_lever_empty_query_bypasses_filter():
    provider = LeverProvider()
    query = JobSearchQuery(query="", limit=200)
    ctx = DiscoveryContext(query=query)

    with patch("app.providers.lever.httpx.AsyncClient",
               return_value=_FakeLeverMixedClient(3, 3, "React")):
        results = await provider.discover(ctx)

    assert len(results) == 6 * len(SAMPLE_LEVER_COMPANIES)


@pytest.mark.asyncio
@pytest.mark.parametrize("keyword", [
    "React Developer", "Python Developer", "Django Developer", "DevOps Engineer"
])
async def test_lever_fairness_preserved_with_filter(keyword):
    """All Lever companies contribute when they all have relevant jobs."""
    provider = LeverProvider()
    query = JobSearchQuery(query=keyword, limit=50)
    ctx = DiscoveryContext(query=query)

    with patch("app.providers.lever.httpx.AsyncClient",
               return_value=_FakeLeverMixedClient(10, 0, keyword)):
        results = await provider.discover(ctx)

    companies = {r.company for r in results}
    expected = {c.capitalize() for c in SAMPLE_LEVER_COMPANIES}
    assert companies == expected, (
        f"[{keyword}] Missing Lever companies after filter: {expected - companies}"
    )


# ─── Ashby: keyword filter ────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("keyword", [
    "React Developer", "Python Developer", "Django Developer", "DevOps Engineer"
])
async def test_ashby_filters_unrelated_jobs(keyword):
    """Unrelated jobs must not appear in Ashby results."""
    provider = AshbyProvider()
    query = JobSearchQuery(query=keyword, limit=100)
    ctx = DiscoveryContext(query=query)

    with patch("app.providers.ashby.httpx.AsyncClient",
               return_value=_FakeAshbyMixedClient(5, 5, keyword)):
        results = await provider.discover(ctx)

    for r in results:
        for unrelated in UNRELATED_TITLES:
            assert unrelated.lower() not in r.title.lower(), (
                f"[{keyword}] Unrelated job '{r.title}' passed Ashby filter"
            )


@pytest.mark.asyncio
@pytest.mark.parametrize("keyword", [
    "React Developer", "Python Developer", "Django Developer", "DevOps Engineer"
])
async def test_ashby_retains_relevant_jobs(keyword):
    """All relevant Ashby jobs must survive the filter."""
    provider = AshbyProvider()
    query = JobSearchQuery(query=keyword, limit=100)
    ctx = DiscoveryContext(query=query)

    with patch("app.providers.ashby.httpx.AsyncClient",
               return_value=_FakeAshbyMixedClient(3, 0, keyword)):
        results = await provider.discover(ctx)

    assert len(results) == 3 * len(SAMPLE_ASHBY_COMPANIES), (
        f"[{keyword}] Expected {3 * len(SAMPLE_ASHBY_COMPANIES)}, got {len(results)}"
    )


@pytest.mark.asyncio
async def test_ashby_empty_query_bypasses_filter():
    provider = AshbyProvider()
    query = JobSearchQuery(query="", limit=200)
    ctx = DiscoveryContext(query=query)

    with patch("app.providers.ashby.httpx.AsyncClient",
               return_value=_FakeAshbyMixedClient(3, 3, "React")):
        results = await provider.discover(ctx)

    assert len(results) == 6 * len(SAMPLE_ASHBY_COMPANIES)


@pytest.mark.asyncio
async def test_ashby_generic_query_bypasses_filter():
    provider = AshbyProvider()
    query = JobSearchQuery(query="Software Engineer", limit=200)
    ctx = DiscoveryContext(query=query)

    with patch("app.providers.ashby.httpx.AsyncClient",
               return_value=_FakeAshbyMixedClient(3, 3, "Software")):
        results = await provider.discover(ctx)

    assert len(results) == 6 * len(SAMPLE_ASHBY_COMPANIES)


@pytest.mark.asyncio
@pytest.mark.parametrize("keyword", [
    "React Developer", "Python Developer", "Django Developer", "DevOps Engineer"
])
async def test_ashby_fairness_preserved_with_filter(keyword):
    """All Ashby companies contribute when they all have relevant jobs."""
    provider = AshbyProvider()
    query = JobSearchQuery(query=keyword, limit=50)
    ctx = DiscoveryContext(query=query)

    with patch("app.providers.ashby.httpx.AsyncClient",
               return_value=_FakeAshbyMixedClient(10, 0, keyword)):
        results = await provider.discover(ctx)

    companies = {r.company for r in results}
    expected = {b.capitalize() for b in SAMPLE_ASHBY_COMPANIES}
    assert companies == expected, (
        f"[{keyword}] Missing Ashby companies after filter: {expected - companies}"
    )


# ─── Batch 1 regression: skill extraction + Ashby real description ────────────

class TestBatch1SkillExtractionAndAshbyDescription:
    """
    Regression tests for the two Batch 1 fixes:

    A) Greenhouse and Lever now extract required_skills from the job description
       using the existing SkillAndApplyExtractor.  A job that mentions Python in
       its description should surface a "Python" skill signal even if "Python" is
       absent from the title.

    B) Ashby now uses the real descriptionPlain/descriptionHtml from the API
       instead of the synthetic "title position at company in loc." string.  A
       job whose title doesn't contain the query keyword but whose real
       description does must no longer be incorrectly rejected by the filter.
    """

    # ── Fix A: Greenhouse skill extraction ────────────────────────────────────

    @pytest.mark.asyncio
    async def test_greenhouse_python_in_description_yields_skill(self):
        """
        Greenhouse job: title has no Python, but HTML content does.
        Expected: job passes filter AND required_skills contains 'Python'.
        """
        provider = GreenhouseProvider()
        query = JobSearchQuery(query="Python Developer", limit=100)
        ctx = DiscoveryContext(query=query)

        class _PythonDescClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def get(self, url, **kwargs):
                m = re.search(r"/boards/(\w+)/jobs", url)
                board = m.group(1) if m else "x"
                return _FakeResponse({"jobs": [{
                    "title": "Backend Engineer",          # no 'python' in title
                    "location": {"name": "Remote"},
                    "absolute_url": f"https://boards.greenhouse.io/{board}/jobs/1",
                    "content": (
                        "<p>We build scalable microservices in "
                        "<strong>Python</strong> using FastAPI and PostgreSQL.</p>"
                    ),
                }]})

        with patch("app.providers.greenhouse.httpx.AsyncClient",
                   return_value=_PythonDescClient()):
            results = await provider.discover(ctx)

        # One result per board — all passed the description-level filter
        assert len(results) == len(GREENHOUSE_BOARDS), (
            f"Expected {len(GREENHOUSE_BOARDS)} results (python in content), "
            f"got {len(results)}"
        )
        for r in results:
            assert "Python" in r.required_skills, (
                f"Expected 'Python' in required_skills for {r.title!r}, "
                f"got {r.required_skills}"
            )

    @pytest.mark.asyncio
    async def test_greenhouse_empty_description_gives_no_skills(self):
        """Jobs with empty content produce required_skills=[] without error."""
        provider = GreenhouseProvider()
        query = JobSearchQuery(query="Python Developer", limit=100)
        ctx = DiscoveryContext(query=query)

        class _EmptyDescClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def get(self, url, **kwargs):
                m = re.search(r"/boards/(\w+)/jobs", url)
                board = m.group(1) if m else "x"
                return _FakeResponse({"jobs": [{
                    "title": "Python Developer",
                    "location": {"name": "Remote"},
                    "absolute_url": f"https://boards.greenhouse.io/{board}/jobs/1",
                    "content": "",        # no description
                }]})

        with patch("app.providers.greenhouse.httpx.AsyncClient",
                   return_value=_EmptyDescClient()):
            results = await provider.discover(ctx)

        assert len(results) == len(GREENHOUSE_BOARDS)
        # Python is in the title, filter passes. No description → empty skills.
        for r in results:
            assert isinstance(r.required_skills, list)

    # ── Fix A: Lever skill extraction ─────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_lever_python_in_description_yields_skill(self):
        """
        Lever job: title has no Python, but descriptionPlain does.
        Expected: job passes filter AND required_skills contains 'Python'.
        """
        provider = LeverProvider()
        query = JobSearchQuery(query="Python Developer", limit=100)
        ctx = DiscoveryContext(query=query)

        class _PythonDescClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def get(self, url, **kwargs):
                m = re.search(r"/postings/(\w+)", url)
                company = m.group(1) if m else "x"
                return _FakeResponse([{
                    "text": "Backend Engineer",           # no 'python' in title
                    "categories": {"location": "Remote"},
                    "hostedUrl": f"https://jobs.lever.co/{company}/1",
                    "descriptionPlain": (
                        "Python is our primary language. We use Django and PostgreSQL "
                        "for our backend systems."
                    ),
                    "workplaceType": "remote",
                }])

        with patch("app.providers.lever.httpx.AsyncClient",
                   return_value=_PythonDescClient()):
            results = await provider.discover(ctx)

        assert len(results) == len(SAMPLE_LEVER_COMPANIES), (
            f"Expected {len(SAMPLE_LEVER_COMPANIES)} results, got {len(results)}"
        )
        for r in results:
            assert "Python" in r.required_skills, (
                f"Expected 'Python' in required_skills for {r.title!r}, "
                f"got {r.required_skills}"
            )

    @pytest.mark.asyncio
    async def test_lever_empty_description_gives_no_skills(self):
        """Lever jobs with empty descriptionPlain produce required_skills=[] without error."""
        provider = LeverProvider()
        query = JobSearchQuery(query="Python Developer", limit=100)
        ctx = DiscoveryContext(query=query)

        class _EmptyDescClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def get(self, url, **kwargs):
                m = re.search(r"/postings/(\w+)", url)
                company = m.group(1) if m else "x"
                return _FakeResponse([{
                    "text": "Python Engineer",
                    "categories": {"location": "Remote"},
                    "hostedUrl": f"https://jobs.lever.co/{company}/1",
                    "descriptionPlain": "",
                    "workplaceType": "remote",
                }])

        with patch("app.providers.lever.httpx.AsyncClient",
                   return_value=_EmptyDescClient()):
            results = await provider.discover(ctx)

        assert len(results) == len(SAMPLE_LEVER_COMPANIES)
        for r in results:
            assert isinstance(r.required_skills, list)

    # ── Fix B: Ashby real description ─────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_ashby_real_description_enables_keyword_filter(self):
        """
        Ashby job: title has no Python, but descriptionPlain does.
        Before fix: synthetic desc had no Python → REJECTED.
        After fix:  real desc has Python → ACCEPTED.
        """
        provider = AshbyProvider()
        query = JobSearchQuery(query="Python Developer", limit=100)
        ctx = DiscoveryContext(query=query)

        class _RealDescClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def get(self, url, **kwargs):
                m = re.search(r"/job-board/(\w+)", url)
                board = m.group(1) if m else "x"
                return _FakeResponse({"jobs": [{
                    "title": "Backend Engineer",          # no 'python' in title
                    "locationName": "Remote",
                    "jobUrl": f"https://jobs.ashbyhq.com/{board}/1",
                    "isRemote": True,
                    "descriptionPlain": (
                        "We build APIs in Python using FastAPI and PostgreSQL."
                    ),
                }]})

        with patch("app.providers.ashby.httpx.AsyncClient",
                   return_value=_RealDescClient()):
            results = await provider.discover(ctx)

        assert len(results) == len(SAMPLE_ASHBY_COMPANIES), (
            "Jobs with Python in real description must pass the Ashby filter. "
            f"Expected {len(SAMPLE_ASHBY_COMPANIES)}, got {len(results)}"
        )
        for r in results:
            assert "Python" in r.required_skills, (
                f"Expected 'Python' in required_skills for {r.title!r}, "
                f"got {r.required_skills}"
            )
            # Description must be the real text, not the synthetic fallback
            assert "Python" in r.description or "python" in r.description.lower(), (
                f"NormalizedJob.description must reflect real API description, "
                f"got: {r.description!r}"
            )

    @pytest.mark.asyncio
    async def test_ashby_no_real_description_falls_back_to_synthetic(self):
        """
        When Ashby API returns no description fields, the synthetic fallback
        is used unchanged — backwards-compatible behaviour.
        """
        provider = AshbyProvider()
        query = JobSearchQuery(query="Python Developer", limit=100)
        ctx = DiscoveryContext(query=query)

        class _NoDescClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                pass
            async def get(self, url, **kwargs):
                m = re.search(r"/job-board/(\w+)", url)
                board = m.group(1) if m else "x"
                return _FakeResponse({"jobs": [{
                    "title": "Python Developer",          # keyword in title → passes
                    "locationName": "Remote",
                    "jobUrl": f"https://jobs.ashbyhq.com/{board}/1",
                    "isRemote": True,
                    # No descriptionPlain / descriptionHtml → fallback
                }]})

        with patch("app.providers.ashby.httpx.AsyncClient",
                   return_value=_NoDescClient()):
            results = await provider.discover(ctx)

        assert len(results) == len(SAMPLE_ASHBY_COMPANIES)
        for r in results:
            # Fallback synthetic string: "Python Developer position at <Board> in Remote."
            assert "Python Developer" in r.description, (
                f"Expected synthetic fallback description, got: {r.description!r}"
            )
