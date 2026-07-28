"""
End-to-end pipeline debug script - AFTER FIXES.
Tests the full pipeline from query enrichment through job extraction.
"""
import asyncio
import sys
import os
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, '.')

async def main():
    print("=" * 80)
    print("PIPELINE DEBUG - After Fixes")
    print("=" * 80)

    # -- Stage 1: Query Enrichment --
    print("\n-- STAGE 1: Query Enrichment --")
    from app.services.search_query_generator import SearchQueryGenerator
    
    for test_q in ["react", "react developer", "python", "django backend"]:
        queries = SearchQueryGenerator.generate_search_engine_queries(test_q)
        print(f"  '{test_q}' -> {queries[:3]} ...")
    
    # Use a simple query
    queries = SearchQueryGenerator.generate_search_engine_queries("react")
    print(f"\n  Full queries for 'react':")
    for i, q in enumerate(queries):
        print(f"    [{i+1}] {q}")

    # -- Stage 2: Search Engine --
    print("\n-- STAGE 2: DuckDuckGo Search --")
    from app.providers.search_engine.duckduckgo_search import DuckDuckGoSearchProvider
    ddg = DuckDuckGoSearchProvider()
    
    test_query = queries[0]  # "react developer jobs"
    print(f"  Query: '{test_query}'")
    results = await ddg.search(test_query, limit=10)
    print(f"  -> {len(results)} URLs returned:")
    for r in results:
        print(f"    {r.url}")
    
    if not results:
        print("  !! DuckDuckGo returned 0 results. STOP.")
        return

    # -- Stage 3: CrawlScheduler --
    print("\n-- STAGE 3: CrawlScheduler --")
    from app.services.crawl.crawl_scheduler import CrawlScheduler
    from app.services.crawl.url_utils import URLDeduplicator
    
    scheduler = CrawlScheduler()
    dedup = URLDeduplicator()
    candidate_urls = [r.url for r in results[:5]]
    
    print(f"  Scheduling {len(candidate_urls)} candidates...")
    job_urls = await scheduler.schedule(candidate_urls, dedup)
    
    print(f"\n  -> CrawlScheduler returned {len(job_urls)} job posting URLs:")
    for u in job_urls[:10]:
        print(f"    {u}")
    
    if not job_urls:
        print("  !! CrawlScheduler returned 0 URLs. STOP.")
        return

    # -- Stage 4: Job Extraction --
    print("\n-- STAGE 4: Job Extraction (first 3 URLs) --")
    from app.services.job_extractor import JobExtractor
    extractor = JobExtractor()
    
    successes = 0
    for url in job_urls[:3]:
        print(f"\n  Extracting: {url}")
        try:
            job = await extractor.extract_from_url(url=url, skip_classification=True)
            if job:
                print(f"    SUCCESS: '{job.title}' at '{job.company}'")
                successes += 1
            else:
                print(f"    NONE returned")
        except Exception as e:
            print(f"    ERROR: {e}")

    print("\n" + "=" * 80)
    print(f"RESULT: {successes} / {min(3, len(job_urls))} jobs extracted")
    print("=" * 80)

asyncio.run(main())
