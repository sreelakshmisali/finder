"""
5-Query Empirical Evidence Protocol Script (Phase 1)

Runs job searches across 5 representative technical queries:
1. React Developer
2. Python Developer
3. Django Developer
4. DevOps Engineer
5. Data Engineer

Saves JSON trace artifacts to backend/logs/search_diagnostics/ and outputs pipeline statistics.
"""

import asyncio
import logging
import sys
import os

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database.base import Base
from app.services.job_service import JobService
from app.schemas.job import JobSearchQuery

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

TEST_QUERIES = [
    "React Developer",
    "Python Developer",
    "Django Developer",
    "DevOps Engineer",
    "Data Engineer"
]


async def run_protocol():
    print("=" * 70)
    print("STARTING 5-QUERY EMPIRICAL EVIDENCE GATHERING PROTOCOL")
    print("=" * 70)

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        service = JobService(db)

        for query_str in TEST_QUERIES:
            print(f"\n>>> Executing Search Query: '{query_str}' (limit=50)")
            search_query = JobSearchQuery(query=query_str, limit=50)
            
            try:
                response = await service.search_jobs(query=search_query)
                print(f"[OK] Query '{query_str}' finished: returned {len(response.jobs)} jobs")
            except Exception as exc:
                print(f"[FAIL] Query '{query_str}' failed with error: {exc}")

    print("\n" + "=" * 70)
    print("5-QUERY PROTOCOL COMPLETED SUCCESSFULLY")
    print("Inspect JSON trace files in backend/logs/search_diagnostics/")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_protocol())
