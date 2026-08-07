import httpx
import re

async def test_ddg_quotes():
    url = "https://lite.duckduckgo.com/lite/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Finder/1.0"}
    queries = [
        'site:boards.greenhouse.io Python Developer',
        'site:boards.greenhouse.io "Python Developer"',
        'site:jobs.lever.co Python Developer',
        'site:jobs.ashbyhq.com Python Developer',
    ]
    async with httpx.AsyncClient() as client:
        for q in queries:
            resp = await client.post(url, data={"q": q}, headers=headers)
            matches = []
            for m in re.finditer(r'<a[^>]+href=[\'"]([^\'"]+)[\'"][^>]+class=[\'"]result-link[\'"][^>]*>(.*?)</a>', resp.text, re.IGNORECASE):
                matches.append((m.group(1), m.group(2)))
            print(f"Query: '{q}' -> Status: {resp.status_code}, Matches: {len(matches)}")
            for u, t in matches[:3]:
                print(f"   - {u}")

import asyncio
asyncio.run(test_ddg_quotes())
