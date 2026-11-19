import asyncio, sys, os, logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.DEBUG, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

async def trace_infopark():
    from app.providers.search_engine.duckduckgo_search import DuckDuckGoSearchProvider
    provider = DuckDuckGoSearchProvider()
    
    # Check if DuckDuckGo returns any infopark results for our new query
    print("=== Testing: site:infopark.in python developer ===")
    results = await provider.search("site:infopark.in python developer", limit=10)
    print(f"Results count: {len(results)}")
    for r in results:
        print(f"  URL: {r.url}")
        print(f"  Title: {r.title}")
    
    print()
    print("=== Testing: site:technopark.in python developer ===")
    results2 = await provider.search("site:technopark.in python developer", limit=10)
    print(f"Results count: {len(results2)}")
    for r in results2:
        print(f"  URL: {r.url}")
        print(f"  Title: {r.title}")
        
    # Also test the known Infopark URL directly
    print()
    print("=== Tracing known Infopark URL through classifiers ===")
    known_url = "https://infopark.in/company-jobs/details/378/25166"
    
    from app.services.crawl.provider_classifier import ProviderClassifier
    provider_tag = ProviderClassifier.classify(known_url)
    print(f"ProviderClassifier tag: {provider_tag}")
    
    from app.services.classification.page_type_classifier import RuleBasedJobPageClassifier
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(known_url, headers={"User-Agent": "Mozilla/5.0"})
            html = resp.text
            print(f"HTTP status: {resp.status_code}")
            print(f"HTML length: {len(html)} chars")
            classification = RuleBasedJobPageClassifier.classify(known_url, html)
            print(f"RuleBasedJobPageClassifier: type={classification.page_type}, conf={classification.confidence:.2f}")
    except Exception as e:
        print(f"Failed to fetch known URL: {e}")

asyncio.run(trace_infopark())
