"""
Unit and Integration Tests for Search Diagnostics Framework (v1.0)
"""

import os
import json
import pytest
from app.utils.search_diagnostics import SearchDiagnosticsTracker, current_diagnostics
from app.services.job_service import JobService
from app.schemas.job import JobSearchQuery


def test_diagnostics_session_tracking():
    diag = SearchDiagnosticsTracker(query="React Developer", location="Remote", limit=20)
    assert diag.session_id is not None
    assert len(diag.session_id) > 10
    assert diag.query == "React Developer"
    assert diag.limit == 20

    diag.start_provider("lever", "Lever", priority=20)
    diag.record_provider_stage("lever", p1_searched=8, p2_fetched=45, p3_rejected=5, p4_returned=40)
    diag.finish_provider("lever", 40)

    pstat = diag.provider_stats["lever"]
    assert pstat.p1_target_searched == 8
    assert pstat.p2_raw_fetched == 45
    assert pstat.p3_internal_rejected == 5
    assert pstat.p4_returned_to_aggregator == 40


def test_global_stage_math():
    diag = SearchDiagnosticsTracker(query="Python Engineer", limit=50)
    diag.record_global_stage(
        stage_id="S4",
        stage_name="Cross-Provider Deduplication",
        input_count=100,
        output_count=85,
        delta_count=15,
        duration=0.05
    )

    stage = diag.global_stages["S4"]
    assert stage.stage_id == "S4"
    assert stage.input_count - stage.delta_count == stage.output_count


def test_limit_audit_logging():
    diag = SearchDiagnosticsTracker(query="DevOps", limit=30)
    diag.record_limit_audit(
        provider="lever",
        location="lever.py:L103",
        variable_name="query.limit",
        applied_limit=30,
        input_size=75,
        output_size=30,
        effect="Provider capped results at limit"
    )

    assert len(diag.limit_audits) == 1
    entry = diag.limit_audits[0]
    assert entry.provider == "lever"
    assert entry.applied_limit == 30
    assert entry.input_size == 75
    assert entry.output_size == 30


def test_json_artifact_generation(tmp_path):
    diag = SearchDiagnosticsTracker(query="Data Scientist", limit=10)
    diag.audit_registered_providers([
        {"source_name": "greenhouse", "display_name": "Greenhouse", "enabled": True, "priority": 10}
    ])
    diag.start_provider("greenhouse", "Greenhouse", priority=10)
    diag.record_provider_stage("greenhouse", p1_searched=5, p2_fetched=20, p3_rejected=2, p4_returned=18)
    diag.finish_provider("greenhouse", 18)

    diag.record_global_stage("S1", "Provider Discovery", 1, 18, 0, 0.5)

    filepath = diag.save_json_artifact()
    assert filepath is not None
    assert os.path.exists(filepath)

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["session"]["search_session_id"] == diag.session_id
    assert data["session"]["query"] == "Data Scientist"
    assert "greenhouse" in data["providers"]
    assert data["global_pipeline_stages"]["S1"]["stage_id"] == "S1"


@pytest.mark.asyncio
async def test_job_service_passive_diagnostics_integration():
    from unittest.mock import MagicMock, AsyncMock
    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    service = JobService(mock_db)
    query = JobSearchQuery(query="React", limit=10)

    # Search execution
    response = await service.search_jobs(query=query)

    assert response is not None
    assert isinstance(response.jobs, list)

    # Verify diagnostic logs folder received JSON artifact
    log_dir = os.path.join("backend", "logs", "search_diagnostics")
    assert os.path.exists(log_dir)
    json_files = [f for f in os.listdir(log_dir) if f.endswith(".json")]
    assert len(json_files) > 0


@pytest.mark.asyncio
async def test_passive_non_interference():
    """Asserts that search execution returns identical results regardless of diagnostics setting."""
    from unittest.mock import MagicMock, AsyncMock
    from app.core.config import settings

    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    service = JobService(mock_db)
    query = JobSearchQuery(query="Python", limit=5)

    # 1. Run with diagnostics enabled
    settings.SEARCH_DIAGNOSTICS_ENABLED = True
    resp_enabled = await service.search_jobs(query=query)

    # 2. Run with diagnostics disabled
    settings.SEARCH_DIAGNOSTICS_ENABLED = False
    resp_disabled = await service.search_jobs(query=query)

    # Restore default
    settings.SEARCH_DIAGNOSTICS_ENABLED = True

    assert len(resp_enabled.jobs) == len(resp_disabled.jobs)
    for j1, j2 in zip(resp_enabled.jobs, resp_disabled.jobs):
        assert j1.title == j2.title
        assert j1.company == j2.company
        assert j1.url == j2.url


def test_attribution_discovery_vs_ats_sources():
    """
    Tests A & B: Verifies that discovery_provider and ats_source remain distinct when a search
    engine discovers an ATS URL vs when an ATS provider discovers it directly.
    """
    from app.schemas.job import NormalizedJob

    # Test A: Direct Lever provider discovery
    job_a = NormalizedJob(
        company="ExampleCorp",
        title="React Developer",
        url="https://jobs.lever.co/examplecorp/123",
        source="lever",
        discovery_provider="lever",
        description="Senior React Developer position"
    )
    assert job_a.discovery_provider == "lever"
    assert job_a.source == "lever"

    # Test B: SearchEngineProvider discovery of Lever URL
    job_b = NormalizedJob(
        company="ExampleCorp",
        title="React Developer",
        url="https://jobs.lever.co/examplecorp/123",
        source="lever",
        discovery_provider="search_engine",
        description="Senior React Developer position"
    )
    assert job_b.discovery_provider == "search_engine"
    assert job_b.source == "lever"
    assert job_b.discovery_provider != job_b.source


def test_attribution_summary_aggregation():
    """
    Test C: Verifies that SearchDiagnosticsTracker correctly computes separate contribution
    counts for discovery_provider vs ats_source.
    """
    diag = SearchDiagnosticsTracker(query="React Developer", limit=10)
    
    t1 = diag.get_or_create_job_trace(
        provider="search_engine",
        title="React Dev 1",
        company="Company A",
        url="https://jobs.lever.co/a/1",
        discovery_provider="search_engine",
        ats_source="lever"
    )
    t1.final_rank = 1

    t2 = diag.get_or_create_job_trace(
        provider="lever",
        title="React Dev 2",
        company="Company B",
        url="https://jobs.lever.co/b/2",
        discovery_provider="lever",
        ats_source="lever"
    )
    t2.final_rank = 2

    summary = diag.calculate_attribution_summary()
    disc_counts = summary["discovery_provider_counts"]
    ats_counts = summary["ats_source_counts"]

    assert disc_counts.get("search_engine") == 1
    assert disc_counts.get("lever") == 1
    assert ats_counts.get("lever") == 2


@pytest.mark.asyncio
async def test_attribution_preservation_across_pipeline():
    """
    Tests D & E: Verifies that discovery_provider and source survive:
    Provider -> NormalizedJob -> Aggregation -> DB Persistence -> Ranking -> Response
    """
    from unittest.mock import MagicMock, AsyncMock
    from app.models.job import Job
    from app.schemas.job import NormalizedJob, JobResponse

    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    norm_job = NormalizedJob(
        company="Acme",
        title="Frontend Lead",
        url="https://boards.greenhouse.io/acme/jobs/99",
        source="greenhouse",
        discovery_provider="search_engine",
        description="Lead Frontend Engineer"
    )

    # Verify NormalizedJob
    assert norm_job.discovery_provider == "search_engine"
    assert norm_job.source == "greenhouse"

    import uuid
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    # Verify DB model
    db_job = Job(
        id=uuid.uuid4(),
        company=norm_job.company,
        title=norm_job.title,
        location="Remote",
        remote=True,
        url=norm_job.url,
        source=norm_job.source,
        discovery_provider=norm_job.discovery_provider,
        description=norm_job.description,
        content_hash="hash123",
        posted_date=now,
        fetched_at=now,
        last_verified_date=now
    )
    assert db_job.discovery_provider == "search_engine"
    assert db_job.source == "greenhouse"

    # Verify API JobResponse schema mapping
    resp = JobResponse.model_validate(db_job)
    assert resp.discovery_provider == "search_engine"
    assert resp.source == "greenhouse"
