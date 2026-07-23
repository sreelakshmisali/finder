"""
Ashby Job Provider

Implements `JobProvider` for Ashby HQ public posting API.
Fetches public postings from Ashby job boards and transforms them into `NormalizedJob`.
"""

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
        Executes discovery on Ashby public posting API matching DiscoveryContext.
        """
        query = context.query
        results: List[NormalizedJob] = []
        search_kw = (query.query or "").lower()
        search_loc = (query.location or "").lower()

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            for board in SAMPLE_ASHBY_COMPANIES:
                try:
                    url = f"https://api.ashbyhq.com/posting-api/job-board/{board}"
                    resp = await client.get(url)

                    if resp.status_code != 200:
                        continue

                    data = resp.json()
                    jobs_list = data.get("jobs", [])
                    company_name = board.capitalize()

                    for item in jobs_list:
                        title = item.get("title", "")
                        loc = item.get("locationName", "Remote")
                        job_url = item.get("jobUrl", "")
                        is_remote = item.get("isRemote", False) or "remote" in loc.lower() or "remote" in title.lower()
                        desc_info = f"{title} position at {company_name} in {loc}."

                        # Filter keyword
                        if search_kw:
                            if search_kw not in title.lower():
                                continue

                        # Filter location
                        if search_loc:
                            if search_loc not in loc.lower():
                                continue

                        # Filter remote
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

                except Exception as exc:
                    logger.warning(f"Ashby fetch failed for board '{board}': {exc}")
                    continue

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
