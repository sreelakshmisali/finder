"""
Live-pipeline diagnostic: runs the real 'python developer' search through
JobService.search_jobs() using the live DB session and live providers,
then reports the stage counts the task asked for.

Run from backend/:
    .\.venv\Scripts\python.exe diag_live_search.py
"""

import asyncio
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Windows asyncio fix (same as app/main.py)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("playwright").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

logger = logging.getLogger("diag_live_search")


async def run_live_search():
    from app.database.session import get_sessionmaker
    from app.schemas.job import JobSearchQuery
    from app.services.job_service import JobService
    from app.utils.search_diagnostics import current_diagnostics

    SessionLocal = get_sessionmaker()

    query = JobSearchQuery(
        query="python developer",
        location=None,
        remote_only=False,
        limit=20,
        force_refresh=True,   # bypass cache, force full discovery cycle
    )

    logger.info("=" * 70)
    logger.info("LIVE SEARCH: query='python developer'  force_refresh=True")
    logger.info("=" * 70)

    async with SessionLocal() as session:
        service = JobService(session)
        result = await service.search_jobs(query, user_id=None)

    logger.info("\n" + "=" * 70)
    logger.info("LIVE SEARCH RESULTS")
    logger.info("=" * 70)
    logger.info(f"  Final returned  : {result.total}")
    logger.info(f"  Jobs in list    : {len(result.jobs)}")
    if result.jobs:
        logger.info("\n  Returned job titles:")
        for j in result.jobs:
            logger.info(f"    [{j.source}] {j.title} @ {j.company}  (score={j.relevance_score})")
    logger.info("=" * 70)

    return result


if __name__ == "__main__":
    asyncio.run(run_live_search())
