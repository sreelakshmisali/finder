import asyncio, sys, os, logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
logging.basicConfig(level=logging.WARNING)

from app.services.search_query_generator import SearchQueryGenerator

q = "python developer"
queries = SearchQueryGenerator.generate_search_engine_queries(raw_query=q, max_queries=10)
print("=== AFTER: Production query set (max_queries=10) ===")
for i, query in enumerate(queries, 1):
    print(f"  [{i:02d}] {query}")
print(f"\nTotal: {len(queries)} queries")
