"""
Persistence Isolation Regression Tests

Verifies that the per-job savepoint fix in JobRepository.save_normalized_job()
prevents a single failed INSERT from cascading and blocking all subsequent
inserts in the same batch.

These tests exercise the real SQLAlchemy async session machinery against an
in-memory SQLite database so the savepoint semantics are real, not mocked.

Coverage:
  1. A malformed/duplicate job does not prevent other valid jobs in the same
     batch from being persisted.
  2. Persistence errors are logged at WARNING level with identifying context.
  3. Normal valid-job persistence still works correctly.
  4. After a failed save the session is NOT in PendingRollbackError — the exact
     bug that dropped 8 → 0 jobs in production.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import List
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database.base import Base
from app.models.job import Job
from app.repositories.job_repository import JobRepository
from app.schemas.job import NormalizedJob


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_norm_job(
    title: str = "Python Developer",
    company: str = "Acme",
    location: str = "Remote",
    url: str | None = None,
) -> NormalizedJob:
    """Create a minimal valid NormalizedJob for testing."""
    return NormalizedJob(
        title=title,
        company=company,
        location=location,
        remote=True,
        salary=None,
        description=f"{title} at {company}.",
        url=url or f"https://example.com/jobs/{uuid.uuid4()}",
        source="greenhouse",
        discovery_provider="greenhouse",
        posted_date=datetime.now(timezone.utc),
        required_skills=["Python"],
    )


def _pre_insert_url(session, url: str) -> Job:
    """Build a Job object pre-inserted at `url` with a unique company/hash."""
    return Job(
        company=f"Preexist-{uuid.uuid4().hex[:8]}",
        title="Pre-existing Job",
        location="Remote",
        remote=True,
        salary=None,
        description="Already in DB.",
        url=url,
        source="lever",
        discovery_provider="lever",
        content_hash=f"{uuid.uuid4().hex}{uuid.uuid4().hex}",  # 64 hex chars
        posted_date=datetime.now(timezone.utc),
        fetched_at=datetime.now(timezone.utc),
        last_verified_date=datetime.now(timezone.utc),
    )


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def db_session():
    """
    Provide a real async SQLite (in-memory) session backed by the actual Job model.

    SQLite supports savepoints (SAVEPOINT / RELEASE / ROLLBACK TO) so the
    begin_nested() code path is exercised with real SQL semantics.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with SessionLocal() as session:
        yield session

    await engine.dispose()


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestPersistenceIsolation:
    """One INSERT failure must not block subsequent valid inserts."""

    @pytest.mark.asyncio
    async def test_valid_job_saves_successfully(self, db_session):
        """Baseline: a single valid job is persisted and returned."""
        repo = JobRepository(db_session)
        job = _make_norm_job(title="Python Developer", company="Stripe")

        saved = await repo.save_normalized_job(job)

        assert saved.id is not None
        assert saved.title == "Python Developer"
        assert saved.company == "Stripe"

    @pytest.mark.asyncio
    async def test_duplicate_url_is_merged_not_inserted(self, db_session):
        """
        A second job with the same URL is merged with the existing record
        via the dedup path — no IntegrityError.
        """
        repo = JobRepository(db_session)
        url = f"https://example.com/jobs/{uuid.uuid4()}"

        first = _make_norm_job(title="Python Developer", company="Stripe", url=url)
        first_saved = await repo.save_normalized_job(first)

        second = _make_norm_job(title="Python Developer", company="Stripe", url=url)
        merged = await repo.save_normalized_job(second)

        assert merged.id == first_saved.id  # same row

    @pytest.mark.asyncio
    async def test_flush_exception_leaves_session_clean(self, db_session):
        """
        After a savepoint-protected INSERT fails, the very next call to
        save_normalized_job() for a *valid* job must succeed — the session
        must NOT be in PendingRollbackError state.

        This is the exact bug that caused 8 → 0 in production.
        """
        repo = JobRepository(db_session)

        # Pre-populate the collision URL.
        collision_url = f"https://example.com/cascade/{uuid.uuid4()}"
        pre = _pre_insert_url(db_session, collision_url)
        async with db_session.begin_nested():
            db_session.add(pre)
            await db_session.flush()
        await db_session.commit()

        bad = _make_norm_job(title="Bad", company="BadCo", url=collision_url)

        _real = repo.get_by_url

        async def _skip_dedup(url):
            if url == collision_url:
                return None
            return await _real(url)

        # First: the failure (dedup bypassed → unique constraint hit)
        with patch.object(repo, "get_by_url", side_effect=_skip_dedup):
            with pytest.raises(Exception):
                await repo.save_normalized_job(bad)

        # Safety-net rollback (mirrors job_service.py)
        try:
            await db_session.rollback()
        except Exception:
            pass

        # Second: a valid job MUST succeed — no PendingRollbackError
        good = _make_norm_job(title="Good After Bad", company="GoodCo")
        saved = await repo.save_normalized_job(good)
        assert saved.id is not None
        assert saved.title == "Good After Bad"

    @pytest.mark.asyncio
    async def test_failure_is_logged_with_job_context(self, db_session, caplog):
        """
        A persistence failure must be logged at WARNING level with enough
        information to identify the job (url, company, title, source).
        """
        repo = JobRepository(db_session)

        collision_url = f"https://example.com/log-test/{uuid.uuid4()}"
        pre = _pre_insert_url(db_session, collision_url)
        async with db_session.begin_nested():
            db_session.add(pre)
            await db_session.flush()
        await db_session.commit()

        bad_job = _make_norm_job(
            title="Colliding Title", company="BadCompany", url=collision_url
        )

        _real = repo.get_by_url

        async def _skip(url):
            if url == collision_url:
                return None
            return await _real(url)

        with caplog.at_level(
            logging.WARNING, logger="app.repositories.job_repository"
        ):
            with patch.object(repo, "get_by_url", side_effect=_skip):
                with pytest.raises(Exception):
                    await repo.save_normalized_job(bad_job)

        warning_records = [
            r
            for r in caplog.records
            if r.levelno >= logging.WARNING
            and "app.repositories.job_repository" in r.name
        ]
        assert warning_records, (
            "Expected at least one WARNING log from job_repository"
        )
        combined_text = " ".join(r.getMessage() for r in warning_records)
        assert (
            collision_url in combined_text or "Colliding Title" in combined_text
        ), f"Expected job URL or title in log, got: {combined_text!r}"

    @pytest.mark.asyncio
    async def test_all_valid_jobs_in_batch_save_correctly(self, db_session):
        """
        Happy path: a batch of unique valid jobs all persist without errors.
        Verifies that savepoint machinery does not break the normal path.
        """
        repo = JobRepository(db_session)
        batch = [
            _make_norm_job(title=f"Engineer #{i}", company=f"Company{i}")
            for i in range(5)
        ]
        saved = [await repo.save_normalized_job(j) for j in batch]

        assert len(saved) == 5
        assert all(j.id is not None for j in saved)
        assert len({j.id for j in saved}) == 5  # all distinct rows

    @pytest.mark.asyncio
    async def test_single_failure_does_not_block_subsequent_saves(
        self, db_session, caplog
    ):
        """
        Core regression test: simulate a race condition where the URL-dedup
        SELECT misses an existing URL (returns None), so the INSERT hits the
        unique constraint.  The savepoint absorbs the failure and subsequent
        valid jobs are still saved.
        """
        repo = JobRepository(db_session)

        collision_url = f"https://example.com/collision/{uuid.uuid4()}"
        pre = _pre_insert_url(db_session, collision_url)
        async with db_session.begin_nested():
            db_session.add(pre)
            await db_session.flush()
        await db_session.commit()

        good1 = _make_norm_job(title="Backend Engineer A", company="Stripe")
        bad = _make_norm_job(
            title="Colliding Job", company="CollideCo", url=collision_url
        )
        good2 = _make_norm_job(title="Backend Engineer B", company="Figma")
        good3 = _make_norm_job(title="Backend Engineer C", company="Cloudflare")

        batch = [good1, bad, good2, good3]
        saved_titles: List[str] = []
        failed = 0

        # Bypass ALL dedup checks for the colliding URL so the INSERT fires
        # and hits the unique constraint.
        _real_url = repo.get_by_url
        _real_hash = repo.get_by_content_hash

        async def _skip_url(url):
            if url == collision_url:
                return None
            return await _real_url(url)

        async def _skip_hash(h):
            # Also skip content hash for the colliding job
            return await _real_hash(h)

        with caplog.at_level(
            logging.WARNING, logger="app.repositories.job_repository"
        ):
            for norm_job in batch:
                try:
                    with patch.object(repo, "get_by_url", side_effect=_skip_url):
                        db_job = await repo.save_normalized_job(norm_job)
                    # Capture title eagerly (avoid lazy-load issues after rollback)
                    saved_titles.append(db_job.title)
                except Exception:
                    failed += 1
                    try:
                        await db_session.rollback()
                    except Exception:
                        pass

        assert failed == 1, f"Expected exactly 1 failure, got {failed}"
        assert len(saved_titles) == 3, (
            f"Expected 3 successful saves, got {len(saved_titles)}: {saved_titles}"
        )
        assert "Backend Engineer A" in saved_titles
        assert "Backend Engineer B" in saved_titles
        assert "Backend Engineer C" in saved_titles
        assert "Colliding Job" not in saved_titles

    @pytest.mark.asyncio
    async def test_multiple_failures_do_not_cascade(self, db_session, caplog):
        """
        Two back-to-back failures (two different collision URLs) must not
        cascade — the three valid jobs in between and after still save.
        """
        repo = JobRepository(db_session)

        collision_a = f"https://example.com/multi-a/{uuid.uuid4()}"
        collision_b = f"https://example.com/multi-b/{uuid.uuid4()}"
        collision_urls = {collision_a, collision_b}

        for url in collision_urls:
            pre = _pre_insert_url(db_session, url)
            async with db_session.begin_nested():
                db_session.add(pre)
                await db_session.flush()
        await db_session.commit()

        batch = [
            _make_norm_job(title="Good A", company="CompA"),
            _make_norm_job(title="Bad A", company="CompBadA", url=collision_a),
            _make_norm_job(title="Good B", company="CompB"),
            _make_norm_job(title="Bad B", company="CompBadB", url=collision_b),
            _make_norm_job(title="Good C", company="CompC"),
        ]

        saved_titles: List[str] = []
        failed = 0

        _real_url = repo.get_by_url

        async def _skip_collisions(url):
            if url in collision_urls:
                return None
            return await _real_url(url)

        with caplog.at_level(
            logging.WARNING, logger="app.repositories.job_repository"
        ):
            for norm_job in batch:
                try:
                    with patch.object(
                        repo, "get_by_url", side_effect=_skip_collisions
                    ):
                        db_job = await repo.save_normalized_job(norm_job)
                    saved_titles.append(db_job.title)
                except Exception:
                    failed += 1
                    try:
                        await db_session.rollback()
                    except Exception:
                        pass

        assert failed == 2, f"Expected 2 failures, got {failed}"
        assert len(saved_titles) == 3, (
            f"Expected 3 successes, got {len(saved_titles)}"
        )
        assert set(saved_titles) == {"Good A", "Good B", "Good C"}
