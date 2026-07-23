"""
Unit tests for AI Resume Improvement features (Quality Analysis & Job Suggestions).
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ai.mock_provider import MockProvider


def test_ai_resume_quality_analysis():
    provider = MockProvider()

    raw_text = """
    Rahul Sharma
    Email: rahul@example.com
    Phone: +91 98765 43210
    
    Work Experience:
    Worked on backend services using Python and Django. Responsible for building REST APIs.
    Helped team with database queries.
    """

    parsed_data = {
        "full_name": "Rahul Sharma",
        "email": "rahul@example.com",
        "phone": "+91 98765 43210",
        "skills": ["Python", "Django", "REST API"],
        "experience": [{"title": "Software Engineer", "company": "Tech Corp"}]
    }

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(provider.analyze_resume_quality(raw_text, parsed_data))

    assert "quality_score" in result
    assert result["quality_score"] > 0
    assert len(result["missing_skills"]) > 0
    assert len(result["weak_descriptions"]) > 0
    assert len(result["ats_issues"]) >= 0

    print("test_ai_resume_quality_analysis: PASSED")


def test_ai_job_specific_suggestions():
    provider = MockProvider()

    raw_text = "Experienced Python developer with Django and REST API background."
    parsed_data = {
        "skills": ["Python", "Django", "REST API"]
    }

    job_title = "Senior Backend Engineer"
    job_description = "We are seeking a Senior Backend Engineer proficient in Python, FastAPI, PostgreSQL, Docker, and Microservices."

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
        provider.suggest_job_specific_improvements(raw_text, parsed_data, job_title, job_description)
    )

    assert "Python" in result["matching_skills"]
    assert "FastAPI" in result["missing_job_skills"]
    assert len(result["suggested_changes"]) > 0

    print("test_ai_job_specific_suggestions: PASSED")


if __name__ == "__main__":
    test_ai_resume_quality_analysis()
    test_ai_job_specific_suggestions()
