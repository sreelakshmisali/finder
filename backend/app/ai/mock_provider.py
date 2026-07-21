"""
Mock AI Provider

Rule-based offline implementation of `AIProvider`.
Allows running and testing resume parsing & match scoring locally without needing an API key.
"""

import re
import logging
from typing import Dict, Any, List

from app.ai.base import AIProvider
from app.schemas.resume import ParsedResumeData

logger = logging.getLogger(__name__)

# Common tech skills keywords for rule-based extraction
COMMON_TECH_SKILLS = [
    "Python", "JavaScript", "TypeScript", "React", "Node.js", "FastAPI", "Django",
    "SQL", "PostgreSQL", "Docker", "AWS", "Git", "REST APIs", "GraphQL", "TailwindCSS",
    "HTML", "CSS", "Linux", "Kubernetes", "CI/CD", "Java", "C++", "Go", "Rust"
]


class MockProvider(AIProvider):
    """
    Mock AI Provider using regex and keyword extraction.
    """

    @property
    def provider_name(self) -> str:
        return "mock"

    async def parse_resume(self, raw_text: str) -> ParsedResumeData:
        """
        Parses resume text using rule-based keyword matching.
        """
        logger.info("Executing Mock AI resume parser")

        # Extract email via regex
        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", raw_text)
        email = email_match.group(0) if email_match else "candidate@example.com"

        # Extract phone via regex
        phone_match = re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", raw_text)
        phone = phone_match.group(0) if phone_match else "(555) 019-2834"

        # Extract candidate name from first line
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        full_name = lines[0] if lines else "Candidate Name"

        # Identify skills present in text
        matched_skills: List[str] = []
        text_lower = raw_text.lower()
        for skill in COMMON_TECH_SKILLS:
            if skill.lower() in text_lower:
                matched_skills.append(skill)

        if not matched_skills:
            matched_skills = ["Python", "TypeScript", "React", "FastAPI", "SQL", "Git"]

        # Construct sample experience & education
        experience = [
            {
                "title": "Software Engineer",
                "company": "Tech Company",
                "duration": "2022 - Present",
                "description": "Developed web applications and APIs using modern frameworks."
            }
        ]

        education = [
            {
                "degree": "B.S. in Computer Science",
                "institution": "University",
                "year": "2022"
            }
        ]

        return ParsedResumeData(
            full_name=full_name,
            email=email,
            phone=phone,
            skills=matched_skills,
            experience=experience,
            education=education,
            projects=[]
        )

    async def explain_match(
        self,
        resume_data: Dict[str, Any],
        job_title: str,
        company: str,
        job_description: str,
        score: float
    ) -> Dict[str, Any]:
        """
        Generates rule-based match explanation.
        """
        resume_skills = set(s.lower() for s in resume_data.get("skills", []))
        desc_lower = job_description.lower()

        reasons: List[str] = []
        missing: List[str] = []

        for skill in COMMON_TECH_SKILLS:
            if skill.lower() in desc_lower:
                if skill.lower() in resume_skills:
                    reasons.append(f"✓ Strong proficiency in {skill}")
                else:
                    missing.append(skill)

        if not reasons:
            reasons = ["✓ Relevant engineering background", "✓ Technical skills overlap"]

        rec = f"Strong Match ({round(score)}%) — candidate demonstrates key technical requirements." if score >= 70 else f"Moderate Fit ({round(score)}%) — candidate has foundational skills."

        return {
            "reasons": reasons[:4],
            "missing_skills": missing[:3],
            "recommendation": rec
        }
