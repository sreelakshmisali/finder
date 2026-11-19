import asyncio, sys, os, logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

async def trace():
    from app.services.job_extractor import JobExtractor
    extractor = JobExtractor()
    
    # The Simelabs Infopark detail URL
    url = "https://infopark.in/company-jobs/details/378/25166"
    print(f"Tracing: {url}")
    
    result = await extractor.extract_from_url(url)
    if result:
        print(f"SUCCESS: {result.title} at {result.company}")
    else:
        print("RESULT: None (rejected or failed to extract)")
    
    # Also try the listing URL discovered by our new query
    url2 = "https://infopark.in/jobs/simelabs-an-astek-company/python-backend-developer-1"
    print(f"\nTracing listing: {url2}")
    result2 = await extractor.extract_from_url(url2)
    if result2:
        print(f"SUCCESS: {result2.title} at {result2.company}")
    else:
        print("RESULT: None (rejected or failed to extract)")

asyncio.run(trace())
