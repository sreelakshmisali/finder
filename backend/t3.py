import asyncio, sys, os, logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

async def trace():
    from app.services.crawl.provider_classifier import ProviderClassifier
    from app.services.classification.page_type_classifier import PageTypeClassifier
    import httpx
    
    # URLs to test
    known_detail = "https://infopark.in/company-jobs/details/378/25166"
    discovered_listing = "https://infopark.in/jobs/simelabs-an-astek-company/python-backend-developer-1"
    classifier = PageTypeClassifier()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    print(f"\nProvider tag for detail URL: {ProviderClassifier.classify(known_detail)}")
    print(f"Provider tag for listing URL: {ProviderClassifier.classify(discovered_listing)}")
    
    for label, url in [("DISCOVERED LISTING", discovered_listing), ("KNOWN DETAIL", known_detail)]:
        print(f"\n=== {label}: {url} ===")
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                html = resp.text
                print(f"HTTP {resp.status_code}, {len(html)} chars")
                result = classifier.classify(url, html)
                print(f"PageTypeClassifier: type={result.page_type}, conf={result.confidence:.2f}")
        except Exception as e:
            print(f"Fetch error: {e}")

asyncio.run(trace())
