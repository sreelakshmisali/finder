"""
Lever Job Provider

Implements `JobProvider` for Lever ATS public postings API.
Fetches public postings from Lever job boards and transforms them into `NormalizedJob`.
"""

import logging
from typing import List, Optional
from datetime import datetime
import httpx

from app.providers.base import JobProvider
from app.schemas.job import JobSearchQuery, NormalizedJob

logger = logging.getLogger(__name__)

# Sample tech companies using Lever
SAMPLE_LEVER_COMPANIES = [
    "netflix", "spotify", "palantir", "twitch",
    "atlassian", "plaid", "dbt", "roblox"
]


class LeverProvider(JobProvider):
    """
    Job provider for Lever Job Boards.
    """

    @property
    def source_name(self) -> str:
        return "lever"

    @property
    def display_name(self) -> str:
        return "Lever"

    @property
    def description(self) -> str:
        return "Discovers postings from technology companies using Lever ATS."

    async def search(self, query: JobSearchQuery) -> List[NormalizedJob]:
        """
        Queries Lever postings API for sample companies and returns matching normalized jobs.
        """
        results: List[NormalizedJob] = []
        search_kw = (query.query or "").lower()
        search_loc = (query.location or "").lower()

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            for company in SAMPLE_LEVER_COMPANIES:
                try:
                    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
                    resp = await client.get(url)

                    if resp.status_code != 200:
                        continue

                    postings = resp.json()
                    company_name = company.capitalize()

                    for post in postings:
                        title = post.get("text", "")
                        categories = post.get("categories", {})
                        loc = categories.get("location", "Remote")
                        job_url = post.get("hostedUrl", "")
                        desc_text = post.get("descriptionPlain", "") or post.get("description", "")

                        # Filter keyword
                        if search_kw:
                            if search_kw not in title.lower() and search_kw not in desc_text.lower():
                                continue

                        # Filter location
                        if search_loc:
                            if search_loc not in loc.lower():
                                continue

                        # Filter remote
                        work_type = post.get("workplaceType", "").lower()
                        is_remote = "remote" in loc.lower() or work_type == "remote" or "remote" in title.lower()
                        if query.remote_only and not is_remote:
                            continue

                        results.append(
                            NormalizedJob(
                                company=company_name,
                                title=title,
                                location=loc,
                                remote=is_remote,
                                salary=None,
                                description=desc_text or f"{title} position at {company_name}.",
                                url=job_url,
                                source=self.source_name,
                                posted_date=datetime.utcnow()
                            )
                        )

                        if len(results) >= query.limit:
                            break

                except Exception as exc:
                    logger.warning(f"Lever fetch failed for company '{company}': {exc}")
                    continue

                if len(results) >= query.limit:
                    break

        return results

    async def get_details(self, url: str) -> Optional[NormalizedJob]:
        """
        Fetch full details for a Lever URL.
        """
        return None
