"""
AI Provider Interface

Abstract base class defining the contract for AI capabilities in Finder:
1. Resume parsing (extracting structured JSON from plain text).
2. Match explanation (generating clear human-readable reasons for job suitability).

Design Rationale:
By isolating AI calls behind this abstract interface, we can easily swap OpenAI
for Google Gemini, Anthropic Claude, or local Ollama models without modifying business logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from app.schemas.resume import ParsedResumeData


class AIProvider(ABC):
    """
    Abstract Base Class for AI services.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Identifier name of the AI provider (e.g. 'openai', 'gemini', 'mock').
        """
        pass

    @abstractmethod
    async def parse_resume(self, raw_text: str) -> ParsedResumeData:
        """
        Extract structured resume details (name, contact, skills, experience, education)
        from unstructured raw text.

        Args:
            raw_text: Plain text extracted from PDF file.

        Returns:
            `ParsedResumeData` Pydantic model with structured fields.
        """
        pass

    @abstractmethod
    async def explain_match(
        self,
        resume_data: Dict[str, Any],
        job_title: str,
        company: str,
        job_description: str,
        score: float
    ) -> Dict[str, Any]:
        """
        Generates human-readable match explanation (reasons, missing skills, recommendation).
        """
        pass

    @abstractmethod
    async def analyze_resume_quality(
        self,
        raw_text: str,
        parsed_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyzes overall resume quality, identifying missing skills, weak descriptions, and ATS issues.

        Returns:
            Dict containing `quality_score`, `missing_skills`, `weak_descriptions`, `ats_issues`, and `summary`.
        """
        pass

    @abstractmethod
    async def suggest_job_specific_improvements(
        self,
        raw_text: str,
        parsed_data: Dict[str, Any],
        job_title: str,
        job_description: str
    ) -> Dict[str, Any]:
        """
        Provides tailored recommendations to customize resume for a target job posting.

        Returns:
            Dict containing `matching_skills`, `missing_job_skills`, `suggested_changes`, and `tailored_summary`.
        """
        pass
