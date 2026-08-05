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

    assert data["search_session_id"] == diag.session_id
    assert data["search_context"]["query"] == "Data Scientist"
    assert "greenhouse" in data["provider_internal_stages"]
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
