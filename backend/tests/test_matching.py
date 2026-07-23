"""
Unit tests for MatchingService (70/30 Resume-Primary Hybrid Matching Engine).
"""

import asyncio
import uuid
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.job import Job
from app.services.matching_service import MatchingService


class DummyJob:
    def __init__(self, title, company, location, remote, description, salary=None):
        self.id = uuid.uuid4()
        self.title = title
        self.company = company
        self.location = location
        self.remote = remote
        self.description = description
        self.salary = salary


class DummyPreferences:
    def __init__(self, work_type="remote", preferred_locations=None, preferred_roles=None, preferred_companies=None, min_salary=100000):
        self.work_type = work_type
        self.preferred_locations = preferred_locations or ["San Francisco", "Remote"]
        self.preferred_roles = preferred_roles or ["Python Developer", "Backend Engineer"]
        self.preferred_companies = preferred_companies or ["Google", "Stripe"]
        self.min_salary = min_salary


def test_matching_calculations():
    service = MatchingService(db=None)

    job = DummyJob(
        title="Senior Python Backend Engineer",
        company="Stripe",
        location="San Francisco, CA",
        remote=True,
        description="Looking for Senior Python Developer with FastAPI, PostgreSQL, Docker, AWS experience.",
        salary="$150,000"
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

    # Verify resume weights (70%) and preference weights (30%)
    assert 0 <= resume_res["weighted"] <= 70.0, "Resume match weighted score must be <= 70"
    assert 0 <= pref_res["weighted"] <= 30.0, "Preference match weighted score must be <= 30"

    total = round(resume_res["weighted"] + pref_res["weighted"], 1)
    assert total > 80.0, f"Strong match candidate should score > 80%, got {total}"
    assert "skills_match" in resume_res
    assert "experience_match" in resume_res
    assert "role_similarity" in resume_res
    assert "tech_overlap" in resume_res

    assert "location_match" in pref_res
    assert "salary_match" in pref_res
    assert "remote_match" in pref_res
    assert "company_match" in pref_res

    print("test_matching_calculations: PASSED")
    print(f"  Calculated Total Score: {total}% (Resume 70%: {resume_res['weighted']} pts, Pref 30%: {pref_res['weighted']} pts)")


if __name__ == "__main__":
    test_matching_calculations()
