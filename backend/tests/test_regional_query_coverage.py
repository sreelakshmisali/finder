import pytest
from app.services.search_query_generator import SearchQueryGenerator


def _prod_queries(raw_query="python developer", location=""):
    """Returns the same 10 queries that search_discovery.py sends in production."""
    return SearchQueryGenerator.generate_search_engine_queries(
        raw_query=raw_query, location=location, max_queries=10)


def test_infopark_query_is_generated():
    """Test 1: site:infopark.in python developer in production set."""
    queries = _prod_queries("python developer")
    assert any("site:infopark.in" in q for q in queries), (
        f"Expected site:infopark.in query in: {queries}")


def test_technopark_query_is_generated():
    """Test 2: site:technopark.in python developer in production set."""
    queries = _prod_queries("python developer")
    assert any("site:technopark.in" in q for q in queries), (
        f"Expected site:technopark.in query in: {queries}")


def test_greenhouse_query_survives():
    """Test 3: site:boards.greenhouse.io still present."""
    queries = _prod_queries("python developer")
    assert any("site:boards.greenhouse.io" in q for q in queries), (
        f"Greenhouse ATS query missing from: {queries}")


def test_lever_query_survives():
    """Test 4: site:jobs.lever.co still present."""
    queries = _prod_queries("python developer")
    assert any("site:jobs.lever.co" in q for q in queries), (
        f"Lever ATS query missing from: {queries}")


def test_ashby_query_survives():
    """Test 5: site:jobs.ashbyhq.com still present."""
    queries = _prod_queries("python developer")
    assert any("site:jobs.ashbyhq.com" in q for q in queries), (
        f"Ashby ATS query missing from: {queries}")


def test_workday_query_survives():
    """Test 6: site:myworkdayjobs.com still present."""
    queries = _prod_queries("python developer")
    assert any("site:myworkdayjobs.com" in q for q in queries), (
        f"Workday ATS query missing from: {queries}")


def test_smartrecruiters_query_survives():
    """Test 7: site:jobs.smartrecruiters.com still present."""
    queries = _prod_queries("python developer")
    assert any("site:jobs.smartrecruiters.com" in q for q in queries), (
        f"SmartRecruiters ATS query missing from: {queries}")


def test_generic_discovery_queries_present():
    """Test 8: At least one broad non-site: query remains."""
    queries = _prod_queries("python developer")
    generic = [q for q in queries if not q.startswith("site:") and not q.startswith('"')]
    assert len(generic) >= 1, f"No generic discovery query found in: {queries}"


def test_production_query_count_within_budget():
    """Test 9: Final slice must be exactly 10 queries (max_queries=10)."""
    queries = _prod_queries("python developer")
    assert len(queries) <= 10, f"Got {len(queries)} queries (> budget): {queries}"
    assert len(queries) == 10, f"Expected 10 but got {len(queries)}: {queries}"


def test_no_duplicate_queries():
    """Test 10: No duplicate query strings allowed."""
    queries = _prod_queries("python developer")
    assert len(queries) == len(set(queries)), (
        f"Duplicate queries found: {[q for q in queries if queries.count(q) > 1]}")


def test_exact_production_query_order_python_developer():
    """Snapshot: exact 10-query allocation = 5 ATS + 2 regional + 2 quoted + 1 broad."""
    queries = _prod_queries("python developer")
    expected = [
        "site:boards.greenhouse.io python developer",
        "site:jobs.lever.co python developer",
        "site:jobs.ashbyhq.com python developer",
        "site:myworkdayjobs.com python developer",
        "site:jobs.smartrecruiters.com python developer",
        "site:infopark.in python developer",
        "site:technopark.in python developer",
        '"python developer" jobs',
        '"python developer" hiring',
        "python developer jobs",
    ]
    assert queries == expected, f"Expected:\n{expected}\nGot:\n{queries}"


def test_regional_queries_include_location():
    """When a non-remote location is given, regional queries carry it."""
    queries = SearchQueryGenerator.generate_search_engine_queries(
        raw_query="python developer", location="Kochi", max_queries=10)
    infopark_q = next((q for q in queries if "site:infopark.in" in q), None)
    technopark_q = next((q for q in queries if "site:technopark.in" in q), None)
    assert infopark_q is not None and "Kochi" in infopark_q, infopark_q
    assert technopark_q is not None and "Kochi" in technopark_q, technopark_q


def test_regional_portals_constant():
    """REGIONAL_JOB_PORTALS must list exactly infopark.in and technopark.in."""
    portals = SearchQueryGenerator.REGIONAL_JOB_PORTALS
    assert "infopark.in" in portals
    assert "technopark.in" in portals
    assert len(portals) == 2, f"Expected 2 portals but found {len(portals)}: {portals}"
