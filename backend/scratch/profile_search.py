import asyncio
import time
import logging

logging.basicConfig(level=logging.INFO)

async def profile_search():
    from app.database.session import get_sessionmaker
    from app.services.job_service import JobService
    from app.schemas.job import JobSearchQuery
    from app.providers.greenhouse import GreenhouseProvider
    from app.providers.lever import LeverProvider
    from app.providers.ashby import AshbyProvider
    from app.providers.search_engine.search_discovery import SearchDiscoveryProvider
    from app.providers.base_discovery import DiscoveryContext

    query = JobSearchQuery(query="python developer", location="remote", limit=50)
    context = DiscoveryContext(query=query)

    print("==========================================")
    print("STARTING SEARCH EXECUTION PROFILING")
    print("==========================================")

    t0 = time.perf_counter()

    # 1. Profile Greenhouse Provider
    tg0 = time.perf_counter()
    gh = GreenhouseProvider()
    gh_jobs = await gh.discover(context)
    tg1 = time.perf_counter()
    print(f"[PROFILER] GreenhouseProvider: {tg1 - tg0:.3f}s (returned {len(gh_jobs)} jobs)")

    # 2. Profile Lever Provider
    tl0 = time.perf_counter()
    lever = LeverProvider()
    lever_jobs = await lever.discover(context)
    tl1 = time.perf_counter()
    print(f"[PROFILER] LeverProvider     : {tl1 - tl0:.3f}s (returned {len(lever_jobs)} jobs)")

    # 3. Profile Ashby Provider
    ta0 = time.perf_counter()
    ashby = AshbyProvider()
    ashby_jobs = await ashby.discover(context)
    ta1 = time.perf_counter()
    print(f"[PROFILER] AshbyProvider     : {ta1 - ta0:.3f}s (returned {len(ashby_jobs)} jobs)")

    # 4. Profile Search Discovery Provider
    ts0 = time.perf_counter()
    sd = SearchDiscoveryProvider()
    sd_jobs = await sd.discover(context)
    ts1 = time.perf_counter()
    print(f"[PROFILER] SearchDiscovery   : {ts1 - ts0:.3f}s (returned {len(sd_jobs)} jobs)")

    # 5. Profile Full JobService (including concurrent execution & DB save)
    session_factory = get_sessionmaker()
    async with session_factory() as db:
        tj0 = time.perf_counter()
        js = JobService(db)
        res = await js.search_jobs(query)
        tj1 = time.perf_counter()
        print(f"[PROFILER] Full JobService   : {tj1 - tj0:.3f}s (returned {res.total} total jobs)")

    t1 = time.perf_counter()
    print(f"[PROFILER] TOTAL BENCHMARK TIME: {t1 - t0:.3f}s")
    print("==========================================")

if __name__ == "__main__":
    asyncio.run(profile_search())
