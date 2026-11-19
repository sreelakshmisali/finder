import asyncio, sys, os, logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.WARNING)

async def trace_infopark():
    # Trace the known Infopark URL
    known_url = "https://infopark.in/company-jobs/details/378/25166"
    job_listing_url = "https://infopark.in/jobs/simelabs-an-astek-company/python-backend-developer-1"
    
    from app.services.crawl.provider_classifier import ProviderClassifier
    print("--- Provider Classification ---")
    print(f"Known URL: {ProviderClassifier.classify(known_url)}")
    print(f"Listing URL: {ProviderClassifier.classify(job_listing_url)}")
    
    from app.services.classification.page_type_classifier import PageTypeClassifier
    import httpx
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    print("\n--- Fetching Infopark listing URL (discovered by new query) ---")
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(job_listing_url, headers=headers)
            html = resp.text
            print(f"HTTP status: {resp.status_code}, length: {len(html)}")
            result = PageTypeClassifier.classify(job_listing_url, html)
            print(f"PageTypeClassifier: type={result.page_type}, conf={result.confidence:.2f}")
    except Exception as e:
        print(f"Error fetching listing: {e}")
    
    print("\n--- Fetching known Infopark detail URL ---")
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(known_url, headers=headers)
            html = resp.text
            print(f"HTTP status: {resp.status_code}, length: {len(html)}")
            result = PageTypeClassifier.classify(known_url, html)
            print(f"PageTypeClassifier: type={result.page_type}, conf={result.confidence:.2f}")
            
            # Also try the JobExtractor classifier
            from app.services.job_extractor import JobExtractor
            extractor = JobExtractor()
            job = await extractor.extract_from_url(known_url)
            if job:
                print(f"JobExtractor: SUCCESS - {job.title} at {job.company}")
            else:
                print("JobExtractor: returned None (rejected by classifier)")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(trace_infopark())
