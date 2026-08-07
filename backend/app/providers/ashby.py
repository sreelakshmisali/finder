"""
Ashby Job Provider

Implements `JobProvider` for Ashby HQ public posting API.
Fetches public postings from Ashby job boards and transforms them into `NormalizedJob`.
"""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime
import httpx

from app.providers.base_discovery import ATSProvider, DiscoveryContext
from app.schemas.job import JobSearchQuery, NormalizedJob

logger = logging.getLogger(__name__)

# Sample companies using Ashby
SAMPLE_ASHBY_COMPANIES = [
    "notion", "linear", "ramp", "resend", "vanta", "pinecone", "posthog"
]


class AshbyProvider(ATSProvider):
    """
    Job provider for Ashby HQ Job Boards.
    """

    @property
    def source_name(self) -> str:
        return "ashby"

    @property
    def display_name(self) -> str:
        return "Ashby"

    @property
    def description(self) -> str:
        return "Discovers postings from fast-growing startups and scaleups using Ashby HQ."

    async def discover(self, context: DiscoveryContext) -> List[NormalizedJob]:
        """
        Executes discovery on Ashby board endpoints matching DiscoveryContext concurrently.
        """
        query = context.query
        results: List[NormalizedJob] = []
        search_kw = (query.query or "").lower()
        search_loc = (query.location or "").lower()

        async def fetch_board(client: httpx.AsyncClient, board: str):
            try:
                url = f"https://api.ashbyhq.com/posting-api/job-board/{board}"
                resp = await client.get(url)
                if resp.status_code == 200:
                    return board, resp.json()
            except Exception as exc:
                logger.warning(f"Ashby fetch failed for board '{board}': {exc}")
            return board, None

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            board_results = await asyncio.gather(*[fetch_board(client, b) for b in SAMPLE_ASHBY_COMPANIES])

        for board, data in board_results:
            if not data or not isinstance(data, dict):
                continue

            company_name = board.capitalize()
            jobs_list = data.get("jobs", [])

            for item in jobs_list:
                title = item.get("title", "")
                loc = item.get("locationName", "Remote")
                job_url = item.get("jobUrl", "")
                desc_info = f"{title} position at {company_name} in {loc}."

                # Filter keyword
                if search_kw:
                    query_terms = [t for t in search_kw.split() if len(t) > 1]
                    text_to_check = f"{title}".lower()
                    if query_terms and not any(t in text_to_check for t in query_terms):
                        continue

                # Filter location
                if search_loc:
                    if search_loc not in loc.lower():
                        continue

                # Filter remote
                is_remote = item.get("isRemote", False) or "remote" in loc.lower() or "remote" in title.lower()
                if query.remote_only and not is_remote:
                    continue

                results.append(
                    NormalizedJob(
                        company=company_name,
                        title=title,
                        location=loc,
                        remote=is_remote,
                        salary=None,
                        description=desc_info,
                        url=job_url,
                        source=self.source_name,
                        posted_date=datetime.utcnow()
                    )
                )

                if len(results) >= query.limit:
                    break

            if len(results) >= query.limit:
                break

        return results

    async def search(self, query: JobSearchQuery) -> List[NormalizedJob]:
        """
        Legacy search method forwarding to discover().
        """
        return await self.discover(DiscoveryContext(query=query))

    async def get_details(self, url: str) -> Optional[NormalizedJob]:
        """
        Fetch full details for an Ashby URL.
        """
        return None
