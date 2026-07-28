"""
Unit tests for MatchingService (100% Resume Compatibility Matching Engine).
"""

import asyncio
import uuid
import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.job import Job
from app.services.matching_service import MatchingService


class DummyJob:
    def __init__(self, title, company, location, remote, description, salary=None, posted_date=None, fetched_at=None, last_verified_date=None):
        self.id = uuid.uuid4()
        self.title = title
        self.company = company
        self.location = location
        self.remote = remote
        self.description = description
        self.salary = salary
        
        now = datetime.now(timezone.utc)
        self.posted_date = posted_date
        self.fetched_at = fetched_at or now
        self.last_verified_date = last_verified_date or self.fetched_at


def test_matching_calculations():
    service = MatchingService(db=None)

    now = datetime.now(timezone.utc)
    job = DummyJob(
        title="Senior Python Backend Engineer",
        company="Stripe",
        location="San Francisco, CA",
        remote=True,
        description="Looking for Senior Python Developer with FastAPI, PostgreSQL, Docker, AWS experience.",
        salary="$150,000",
        posted_date=now - timedelta(days=2),
        last_verified_date=now
    )

    parsed_resume = {
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "experience_years": 6,
        "target_roles": ["Python Developer", "Backend Engineer"]
    }
    raw_text = "Senior Python Developer with 6 years experience building FastAPI backends, PostgreSQL, and Docker."

    resume_res = service._calculate_resume_compatibility(parsed_resume, raw_text, job)

    # Verify resume weights (100%)
    assert 0 <= resume_res["weighted"] <= 100.0, "Resume match weighted score must be <= 100"
    assert resume_res["weighted"] > 80.0, f"Strong match candidate should score > 80%, got {resume_res['weighted']}"

    print("test_matching_calculations: PASSED")
    print(f"  Calculated Total Score: {resume_res['weighted']}%")


if __name__ == "__main__":
    test_matching_calculations()

