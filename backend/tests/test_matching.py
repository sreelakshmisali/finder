"""
Unit tests for MatchingService (70/20/10 Resume/Preference/Freshness Hybrid Matching Engine).
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


class DummyPreferences:
    def __init__(self, work_type="remote", preferred_locations=None, preferred_roles=None, preferred_companies=None, min_salary=100000):
        self.work_type = work_type
        self.preferred_locations = preferred_locations or ["San Francisco", "Remote"]
        self.preferred_roles = preferred_roles or ["Python Developer", "Backend Engineer"]
        self.preferred_companies = preferred_companies or ["Google", "Stripe"]
        self.min_salary = min_salary


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

    preferences = DummyPreferences()

    resume_res = service._calculate_resume_compatibility(parsed_resume, raw_text, job)
    pref_res = service._calculate_preference_alignment(job, preferences)
    fresh_res = service._calculate_freshness(job)

    # Verify resume weights (70%), preference weights (20%), freshness (10%)
    assert 0 <= resume_res["weighted"] <= 70.0, "Resume match weighted score must be <= 70"
    assert 0 <= pref_res["weighted"] <= 20.0, "Preference match weighted score must be <= 20"
    assert 0 <= fresh_res["weighted"] <= 10.0, "Freshness match weighted score must be <= 10"

    total = round(resume_res["weighted"] + pref_res["weighted"] + fresh_res["weighted"], 1)
    assert total > 80.0, f"Strong match candidate should score > 80%, got {total}"

    print("test_matching_calculations: PASSED")
    print(f"  Calculated Total Score: {total}% (Resume: {resume_res['weighted']}, Pref: {pref_res['weighted']}, Fresh: {fresh_res['weighted']})")


def test_freshness_calculations():
    service = MatchingService(db=None)
    now = datetime.now(timezone.utc)
    
    # 1. Very Fresh Job (Posted 1 day ago, Verified today)
    fresh_job = DummyJob("Title", "Co", "Loc", False, "Desc", posted_date=now - timedelta(days=1), last_verified_date=now)
    res_fresh = service._calculate_freshness(fresh_job)
    assert res_fresh["weighted"] >= 9.0  # Should be very close to 10
    
    # 2. Old Job (Posted 30 days ago, Verified 10 days ago)
    old_job = DummyJob("Title", "Co", "Loc", False, "Desc", posted_date=now - timedelta(days=30), last_verified_date=now - timedelta(days=10))
    res_old = service._calculate_freshness(old_job)
    assert res_old["weighted"] < 5.0  # Should be significantly decayed
    
    # 3. Completely Stale Job (Posted 60 days ago, Verified 30 days ago)
    stale_job = DummyJob("Title", "Co", "Loc", False, "Desc", posted_date=now - timedelta(days=60), last_verified_date=now - timedelta(days=30))
    res_stale = service._calculate_freshness(stale_job)
    assert res_stale["weighted"] == 0.0  # Completely decayed
    
    # 4. Missing Posted Date (relies entirely on fetched_at / verified)
    missing_posted_job = DummyJob("Title", "Co", "Loc", False, "Desc", posted_date=None, last_verified_date=now - timedelta(days=2))
    res_missing_posted = service._calculate_freshness(missing_posted_job)
    assert res_missing_posted["weighted"] > 5.0  # Still gets score from verified date
    
    print("test_freshness_calculations: PASSED")


if __name__ == "__main__":
    test_matching_calculations()
    test_freshness_calculations()
