"""
Diagnostic script: exercises save_normalized_job() directly against the live
PostgreSQL database with synthetic "python developer" jobs to surface the exact
exception causing 0 jobs to be saved.

Run from backend/ directory:
    python ../..\.gemini\antigravity\brain\00691c09-4571-499a-93be-36fedd40f177\scratch\diag_db_save.py
or copy to backend/ and run:
    python diag_db_save.py
"""

import asyncio
import sys
import os
import traceback
import logging
from datetime import datetime, timezone

# ── add backend to sys.path ───────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
)

# suppress sqlalchemy noise except errors
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

logger = logging.getLogger("diag_db_save")


SYNTHETIC_PYTHON_JOBS = [
    {
        "company": "Acme Corp",
        "title": "Python Developer",
        "location": "Remote",
        "remote": True,
        "salary": "$90,000 - $120,000",
        "description": "We are looking for an experienced Python developer to join our team. You will build RESTful APIs using FastAPI and SQLAlchemy. Strong knowledge of Python, asyncio, and PostgreSQL required.",
        "url": "https://greenhouse.io/jobs/acme-python-developer-001",
        "source": "greenhouse",
        "discovery_provider": "greenhouse",
        "apply_url": "https://greenhouse.io/jobs/acme-python-developer-001/apply",
        "can_apply": True,
        "posted_date": datetime(2026, 8, 15, tzinfo=timezone.utc),
    },
    {
        "company": "Beta Technologies",
        "title": "Senior Python Engineer",
        "location": "New York, NY",
        "remote": False,
        "salary": None,
        "description": "Senior Python Engineer position at Beta Technologies. Experience with Django, Flask, and microservices architecture required. Python 3.10+.",
        "url": "https://lever.co/beta-technologies/senior-python-engineer-002",
        "source": "lever",
        "discovery_provider": "lever",
        "apply_url": None,
        "can_apply": False,
        "posted_date": datetime(2026, 8, 14, tzinfo=timezone.utc),
    },
    {
        "company": "Gamma AI",
        "title": "Python Backend Developer",
        "location": "San Francisco, CA",
        "remote": True,
        "salary": "$130,000 - $160,000",
        "description": "Python Backend Developer for AI-powered products. You will work on data pipelines, ML model serving, and API development using Python and PyTorch.",
        "url": "https://jobs.ashbyhq.com/gamma-ai/python-backend-dev-003",
        "source": "ashby",
        "discovery_provider": "ashby",
        "apply_url": "https://jobs.ashbyhq.com/gamma-ai/python-backend-dev-003/apply",
        "can_apply": True,
        "posted_date": datetime(2026, 8, 16, tzinfo=timezone.utc),
    },
    {
        "company": "Delta Cloud",
        "title": "Python Developer - Cloud Infrastructure",
        "location": "Austin, TX",
        "remote": True,
        "salary": "$100,000 - $140,000",
        "description": "Join our cloud infrastructure team as a Python Developer. You will automate cloud provisioning with Terraform and Python scripts on AWS.",
        "url": "https://boards.greenhouse.io/delta-cloud/python-developer-cloud-004",
        "source": "greenhouse",
        "discovery_provider": "search_engine",
        "apply_url": "https://boards.greenhouse.io/delta-cloud/python-developer-cloud-004/apply",
        "can_apply": True,
        "posted_date": datetime(2026, 8, 13, tzinfo=timezone.utc),
    },
    {
        "company": "Epsilon Data",
        "title": "Junior Python Developer",
        "location": "Remote",
        "remote": True,
        "salary": None,
        "description": "Entry level Python Developer role at a data analytics company. Work with pandas, numpy, and matplotlib to build dashboards and ETL pipelines.",
        "url": "https://app.lever.co/epsilon-data/junior-python-developer-005",
        "source": "lever",
        "discovery_provider": "lever",
        "apply_url": None,
        "can_apply": False,
        "posted_date": datetime(2026, 8, 12, tzinfo=timezone.utc),
    },
    {
        "company": "Zeta Systems",
        "title": "Python Full Stack Developer",
        "location": "Chicago, IL",
        "remote": False,
        "salary": "$95,000 - $125,000",
        "description": "Full Stack Python Developer combining Django backend with React frontend. You will build internal tools and customer-facing web apps.",
        "url": "https://greenhouse.io/jobs/zeta-systems/python-fullstack-006",
        "source": "greenhouse",
        "discovery_provider": "search_engine",
        "apply_url": "https://greenhouse.io/jobs/zeta-systems/python-fullstack-006/apply",
        "can_apply": True,
        "posted_date": datetime(2026, 8, 11, tzinfo=timezone.utc),
    },
    {
        "company": "Eta Analytics",
        "title": "Python Data Engineer",
        "location": "Remote",
        "remote": True,
        "salary": "$110,000 - $145,000",
        "description": "Python Data Engineer to build scalable data infrastructure with Apache Spark, Kafka, and Airflow. Strong Python and SQL skills required.",
        "url": "https://jobs.ashbyhq.com/eta-analytics/python-data-engineer-007",
        "source": "ashby",
        "discovery_provider": "search_engine",
        "apply_url": None,
        "can_apply": False,
        "posted_date": datetime(2026, 8, 10, tzinfo=timezone.utc),
    },
    {
        "company": "Theta ML",
        "title": "Python ML Engineer",
        "location": "Seattle, WA",
        "remote": True,
        "salary": "$140,000 - $175,000",
        "description": "Machine Learning Engineer primarily using Python. TensorFlow, scikit-learn, and MLflow experience required. You will productionize ML models.",
        "url": "https://lever.co/theta-ml/python-ml-engineer-008",
        "source": "lever",
        "discovery_provider": "search_engine",
        "apply_url": "https://lever.co/theta-ml/python-ml-engineer-008/apply",
        "can_apply": True,
        "posted_date": datetime(2026, 8, 9, tzinfo=timezone.utc),
    },
]


async def run_diagnostics():
    from app.database.session import get_sessionmaker
    from app.repositories.job_repository import JobRepository
    from app.schemas.job import NormalizedJob

    # Minimal context variable mocks so save_normalized_job doesn't crash on tracker/diag
    from contextvars import ContextVar
    from app.utils import pipeline_tracker as pt_module
    from app.utils import search_diagnostics as sd_module

    # Override context vars to return None (avoid AttributeError on None.record_*)
    pt_module.current_tracker = ContextVar("current_tracker", default=None)
    sd_module.current_diagnostics = ContextVar("current_diagnostics", default=None)

    SessionLocal = get_sessionmaker()

    logger.info("=" * 70)
    logger.info("DIAGNOSTIC: DB save loop test with 8 synthetic python-developer jobs")
    logger.info("=" * 70)

    ok_count = 0
    fail_count = 0

    async with SessionLocal() as session:
        repo = JobRepository(session)

        for idx, job_data in enumerate(SYNTHETIC_PYTHON_JOBS, start=1):
            norm_job = NormalizedJob(**job_data)
            logger.info(f"\n{'─'*60}")
            logger.info(f"[JOB {idx}] Attempting save: title={norm_job.title!r} company={norm_job.company!r}")
            logger.info(f"          url={norm_job.url!r}")
            logger.info(f"          source={norm_job.source!r}  discovery_provider={norm_job.discovery_provider!r}")
            logger.info(f"          salary={norm_job.salary!r}  remote={norm_job.remote}")
            logger.info(f"          posted_date={norm_job.posted_date!r}")

            try:
                saved = await repo.save_normalized_job(norm_job)
                ok_count += 1
                logger.info(f"[JOB {idx}] ✅ SAVED OK — db id={saved.id}")
            except Exception as exc:
                fail_count += 1
                logger.error(
                    f"\n[DIAG][JOB {idx}] ❌ DB save FAILED\n"
                    f"  exc_type  = {type(exc).__name__}\n"
                    f"  exc_msg   = {exc!r}\n"
                )
                logger.error(f"[DIAG][JOB {idx}] Full traceback:\n{traceback.format_exc()}")

                # Attempt rollback to isolate root vs cascade failures
                try:
                    await session.rollback()
                    logger.error(f"[DIAG][JOB {idx}] Rollback SUCCEEDED — next job will use clean state")
                except Exception as rb_exc:
                    logger.error(f"[DIAG][JOB {idx}] Rollback also FAILED: {type(rb_exc).__name__}: {rb_exc!r}")

    logger.info("\n" + "=" * 70)
    logger.info(f"DIAGNOSTIC SUMMARY: {ok_count} saved OK, {fail_count} failed out of {len(SYNTHETIC_PYTHON_JOBS)} jobs")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_diagnostics())
