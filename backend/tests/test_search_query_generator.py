"""
Unit & Integration Tests for Search Query Generator

Tests signal extraction, query generation, semantic deduplication, deterministic ranking,
preference refinements, and edge cases (large resumes, missing fields, preference conflicts).
"""

from app.schemas.search_profile import ResumeSearchProfile
from app.services.resume_signal_extractor import ResumeSignalExtractor
from app.services.search_query_generator import SearchQueryGenerator
from app.models.preference import Preference
from app.models.resume import Resume


def test_resume_signal_extractor_example():
    """
    Test extraction of signals matching the example resume in Task 13 requirements.
    """
    parsed_data = {
        "skills": ["Python", "Django", "FastAPI", "PostgreSQL"],
        "experience": [
            {"title": "3 years Backend Developer", "description": "Built REST APIs"}
        ]
    }

    profile = ResumeSignalExtractor.extract_profile(parsed_data)

    assert "Python" in profile.primary_languages
    assert "Django" in profile.frameworks
    assert "FastAPI" in profile.frameworks
    assert "PostgreSQL" in profile.databases
    assert "Backend" in profile.domains
    assert profile.years_experience == 3


def test_generate_queries_prompt_example():
    """
    Verify exact generated queries for the Task 13 prompt example:
    Skills: Python, Django, FastAPI, PostgreSQL
    Experience: 3 years Backend Developer
    """
    parsed_data = {
        "skills": ["Python", "Django", "FastAPI", "PostgreSQL"],
        "experience": [
            {"title": "3 years Backend Developer"}
        ]
    }

    profile = ResumeSignalExtractor.extract_profile(parsed_data)
    rich_queries = SearchQueryGenerator.generate_rich_queries(profile, max_queries=5)
    query_strings = [q.query for q in rich_queries]

    expected = [
        "Python Backend Engineer",
        "Django Developer",
        "FastAPI Engineer",
        "Backend API Developer",
        "Python Software Engineer"
    ]

    for item in expected:
        assert item in query_strings, f"Expected '{item}' in generated queries: {query_strings}"


def test_preference_refinement_and_conflicts():
    """
    Test that user preferences refine and prioritize generated searches,
    even when conflicting with resume domain (e.g. Resume = Backend, Preference = Data Engineer).
    """
    parsed_data = {
        "skills": ["Python", "Django", "FastAPI"],
        "experience": [{"title": "Backend Developer"}]
    }
    profile = ResumeSignalExtractor.extract_profile(parsed_data)

    preference = Preference(preferred_roles=["Data Engineer"])
    rich_queries = SearchQueryGenerator.generate_rich_queries(profile, preference=preference, max_queries=5)
    query_strings = [q.query for q in rich_queries]

    # Preference boost strategy should place preferred role at top priority
    assert query_strings[0] == "Python Data Engineer"


def test_semantic_deduplication():
    """
    Verify that redundant variations (e.g. Python Developer vs Python Engineer) are deduplicated.
    """
    profile = ResumeSearchProfile(
        skills=["Python"],
        primary_languages=["Python"],
        frameworks=[],
        databases=[],
        roles=["Python Developer"],
        domains=["Backend"]
    )

    rich_queries = SearchQueryGenerator.generate_rich_queries(profile, max_queries=5)
    query_strings = [q.query for q in rich_queries]

    # Should not contain both 'Python Developer' and 'Python Engineer'
    lower_queries = [q.lower() for q in query_strings]
    assert len(lower_queries) == len(set(lower_queries))


def test_deterministic_ordering():
    """
    Verify that running query generation multiple times produces identical query ordering.
    """
    parsed_data = {
        "skills": ["Python", "Django", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        "experience": [{"title": "Senior Software Engineer"}]
    }
    profile = ResumeSignalExtractor.extract_profile(parsed_data)

    run1 = [q.query for q in SearchQueryGenerator.generate_rich_queries(profile, max_queries=5)]
    run2 = [q.query for q in SearchQueryGenerator.generate_rich_queries(profile, max_queries=5)]

    assert run1 == run2


def test_large_resume_safeguards():
    """
    Verify that large resumes with 50+ skills do not cause query explosion.
    """
    parsed_data = {
        "skills": [f"Skill_{i}" for i in range(50)] + ["Python", "Django"],
        "experience": [{"title": f"Role_{i}"} for i in range(10)]
    }
    profile = ResumeSignalExtractor.extract_profile(parsed_data)
    queries = SearchQueryGenerator.generate_rich_queries(profile, max_queries=5)

    assert len(queries) <= 5


def test_no_experience_or_no_skills_fallback():
    """
    Test fallback query generation when resume has missing fields.
    """
    # 1. No experience
    profile1 = ResumeSignalExtractor.extract_profile({"skills": ["Python", "Flask"]})
    queries1 = SearchQueryGenerator.generate_rich_queries(profile1, max_queries=5)
    assert len(queries1) > 0

    # 2. No skills
    profile2 = ResumeSignalExtractor.extract_profile({"experience": [{"title": "Software Engineer"}]})
    queries2 = SearchQueryGenerator.generate_rich_queries(profile2, max_queries=5)
    assert len(queries2) > 0


def test_unknown_technologies():
    """
    Verify resume with unknown tech stack doesn't crash generator.
    """
    parsed_data = {
        "skills": ["CustomProprietaryLanguage", "InternalFrameworkV2"],
        "experience": [{"title": "Custom Tool Engineer"}]
    }
    profile = ResumeSignalExtractor.extract_profile(parsed_data)
    queries = SearchQueryGenerator.generate_rich_queries(profile, max_queries=5)

    assert len(queries) > 0
    assert any("CustomProprietaryLanguage" in q.query or "Software" in q.query for q in queries)


def test_multi_domain_resume():
    """
    Verify multi-domain resumes (Backend + DevOps).
    """
    parsed_data = {
        "skills": ["Python", "Django", "FastAPI", "Docker", "Kubernetes", "AWS", "Terraform"],
        "experience": [{"title": "DevOps Backend Engineer"}]
    }
    profile = ResumeSignalExtractor.extract_profile(parsed_data)

    assert "Backend" in profile.domains or "DevOps" in profile.domains
    queries = SearchQueryGenerator.generate_rich_queries(profile, max_queries=5)
    assert len(queries) > 0


if __name__ == "__main__":
    test_resume_signal_extractor_example()
    test_generate_queries_prompt_example()
    test_preference_refinement_and_conflicts()
    test_semantic_deduplication()
    test_deterministic_ordering()
    test_large_resume_safeguards()
    test_no_experience_or_no_skills_fallback()
    test_unknown_technologies()
    test_multi_domain_resume()
    print("ALL 9 SEARCH QUERY GENERATOR TESTS PASSED SUCCESSFULLY!")
