"""
Golden Dataset Unit Tests for Intent Matching Engine & Search Relevance

Verifies QueryIntentParser, TextNormalizer, RoleIntentExtractor, and RelevanceRankingService against
a data-driven matrix of tech, non-tech, and specialized search queries to prevent search regressions.
"""

from datetime import datetime
import pytest

from app.schemas.job import NormalizedJob
from app.services.search.query_intent_parser import QueryIntentParser
from app.services.search.text_normalizer import TextNormalizer
from app.services.search.role_intent_extractor import RoleIntentExtractor, RoleIntent
from app.services.search.relevance_ranking import RelevanceRankingService


def make_job(title: str, company: str = "TestCorp", desc: str = "", skills: list = None) -> NormalizedJob:
    """Helper to construct a test NormalizedJob."""
    return NormalizedJob(
        company=company,
        title=title,
        location="San Francisco, CA",
        remote=True,
        salary="$120,000 - $160,000",
        description=desc or f"{title} position at {company}.",
        url=f"https://example.com/jobs/{title.lower().replace(' ', '-')}",
        source="test",
        required_skills=skills or [],
        posted_date=datetime.utcnow()
    )


class TestTextNormalizer:
    def test_synonym_normalization(self):
        assert TextNormalizer.normalize("Front-End Developer") == "frontend developer"
        assert TextNormalizer.normalize("Sr. JS Engineer") == "senior javascript engineer"
        assert TextNormalizer.normalize("SW Engineer") == "software engineer"
        assert TextNormalizer.normalize("React Native Developer") == "react_native developer"


class TestRoleIntentExtractor:
    def test_extract_react_developer(self):
        intent = RoleIntentExtractor.extract("React Developer", "Building React web components")
        assert "frontend" in intent.domains
        assert "react" in intent.technologies
        assert intent.is_generic is False

    def test_extract_game_developer(self):
        intent = RoleIntentExtractor.extract("Game Developer", "Building mobile games in Unity and React Native")
        assert "game" in intent.domains
        assert "react_native" in intent.technologies
        assert intent.is_generic is False

    def test_extract_generic_software_engineer(self):
        intent = RoleIntentExtractor.extract("Software Engineer", "Building microservices and frontend React apps")
        assert intent.is_generic is True


class TestIntentMatchingEngineGoldenMatrix:
    """
    Data-driven evaluation suite testing query intent relevance ranking, role domain conflicts, and rejection.
    """

    GOLDEN_DATASET = [
        {
            "query": "React Developer",
            "accept": [
                make_job("React Developer", "Stripe", desc="Building UI in React and TypeScript"),
                make_job("Senior Frontend Engineer", "Meta", desc="React, Redux, Next.js web application"),
                make_job("Software Engineer", "Vercel", desc="Frontend software engineer building React components", skills=["React"]),
                make_job("React UI Engineer", "Airbnb", desc="Web UI engineering")
            ],
            "reject": [
                make_job("Game Developer", "Epic Games", desc="Mobile game developer using React Native and Unity"),
                make_job("Unity Developer", "Roblox", desc="Game physics and 3D graphics developer"),
                make_job("Account Manager, Privy", "Stripe", desc="Who we are: Stripe is a financial platform for developers"),
                make_job("Administrative Business Partner", "Stripe", desc="Supporting executive leadership as we build developer tools"),
                make_job("HR Coordinator", "Google", desc="Human resources onboarding specialist")
            ]
        },
        {
            "query": "Backend Engineer",
            "accept": [
                make_job("Python Backend Developer", "Datadog", desc="Building scalable Python microservices"),
                make_job("Senior Backend Engineer", "Cloudflare", desc="Go and Rust systems backend architecture"),
                make_job("Software Engineer II", "Stripe", desc="API platform engineering", skills=["Python", "Go"])
            ],
            "reject": [
                make_job("Sales Executive", "Salesforce", desc="Enterprise software sales representative"),
                make_job("Marketing Manager", "Canva", desc="Digital marketing campaign lead")
            ]
        },
        {
            "query": "Product Manager",
            "accept": [
                make_job("Senior Product Manager", "Linear", desc="Leading core product roadmap"),
                make_job("Product Manager - Growth", "Ramp", desc="Driving user acquisition metrics")
            ],
            "reject": [
                make_job("React Developer", "Vercel", desc="Frontend developer building Next.js components"),
                make_job("Accounting Clerk", "Figma", desc="Financial accounting and bookkeeping")
            ]
        },
        {
            "query": "UX Designer",
            "accept": [
                make_job("Product Designer (UX)", "Figma", desc="UI/UX design and wireframing"),
                make_job("Senior UX Designer", "Notion", desc="User experience research and interaction design")
            ],
            "reject": [
                make_job("Accountant", "Intuit", desc="Corporate financial audit specialist"),
                make_job("Software Engineer", "Docker", desc="Backend C++ system engineer")
            ]
        },
        {
            "query": "Data Scientist",
            "accept": [
                make_job("Machine Learning Engineer", "OpenAI", desc="Training deep learning AI models"),
                make_job("Senior Data Scientist", "Netflix", desc="Statistical analysis and recommendation algorithms")
            ],
            "reject": [
                make_job("Office Administrator", "Slack", desc="Managing office supplies and reception"),
                make_job("Recruiter", "LinkedIn", desc="Talent acquisition and sourcing")
            ]
        }
    ]

    def test_golden_dataset_matrix(self):
        engine = RelevanceRankingService()

        for case in self.GOLDEN_DATASET:
            query = case["query"]
            accept_candidates = case["accept"]
            reject_candidates = case["reject"]

            # Test Accepted Jobs
            accepted, _ = engine.rank_and_filter(accept_candidates, query=query)
            accepted_titles = [j.title for j in accepted]
            for job in accept_candidates:
                assert job.title in accepted_titles, f"Job '{job.title}' should have been accepted for query '{query}'"

            # Test Rejected Jobs
            accepted_for_rejected, rejected_tuples = engine.rank_and_filter(reject_candidates, query=query)
            rejected_titles = [j.title for j in rejected_tuples]
            for job in reject_candidates:
                assert job.title in rejected_titles, f"Job '{job.title}' should have been rejected for query '{query}', but was accepted."
