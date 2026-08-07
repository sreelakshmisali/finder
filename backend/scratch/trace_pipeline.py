import asyncio
import logging
import json
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trace_pipeline")

from app.schemas.job import JobSearchQuery
from app.providers.base_discovery import DiscoveryContext
from app.providers.search_engine.search_discovery import SearchDiscoveryProvider
from app.utils.pipeline_report_generator import PipelineReportGenerator
from app.services.search_query_generator import SearchQueryGenerator

async def main():
    raw_query = "Python Developer"
    print("=" * 80)
    print(f"DIAGNOSTIC PIPELINE TRACE FOR QUERY: '{raw_query}'")
    print("=" * 80)

    # 1. Evaluate Query Generation
    queries = SearchQueryGenerator.generate_search_engine_queries(raw_query=raw_query, location="")
    print("\n--- STAGE 1: GENERATED SEARCH QUERIES ---")
    for i, q in enumerate(queries, 1):
        print(f"  {i:2d}. {q}")

    query = JobSearchQuery(query=raw_query, limit=10)
    context = DiscoveryContext(query=query)
    provider = SearchDiscoveryProvider()

    # Execute search discovery
    results = await provider.discover(context)

    tracker = context.metadata.get("tracker")

    print("\n--- STAGE 2: CANDIDATE RESULTS & AGGREGATOR ---")
    if tracker:
        for q, engines in tracker.stage1_discovery.items():
            print(f"\nQuery: '{q}'")
            for eng, data in engines.items():
                print(f"  Engine [{eng}]: returned {len(data['returned'])} URLs")
                for u in data["returned"][:5]:
                    print(f"    - {u}")

    print("\n--- STAGE 3 & 4: CRAWL SCHEDULER & PAGE CLASSIFICATION ---")
    if tracker:
        for ev in tracker.events:
            if ev["type"] in ("scheduler_decision", "page_classified", "job_extracted"):
                print(f"  Event: {ev['type']} -> {json.dumps({k:v for k,v in ev.items() if k != 'timestamp'})}")

    print("\n--- FINAL RETURNED NORMALIZED JOBS ---")
    print(f"Total jobs returned: {len(results)}")
    for idx, job in enumerate(results, 1):
        print(f"\n  Job #{idx}:")
        print(f"    Title   : {job.title}")
        print(f"    Company : {job.company}")
        print(f"    Location: {job.location}")
        print(f"    Source  : {job.source}")
        print(f"    URL     : {job.url}")
        print(f"    ApplyURL: {job.apply_url}")
        print(f"    Desc (first 120 chars): {job.description[:120]}...")

    if tracker:
        report = PipelineReportGenerator.generate_report(tracker)
        print("\n" + report)

if __name__ == "__main__":
    asyncio.run(main())
