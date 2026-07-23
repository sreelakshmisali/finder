"""
OpenAI AI Provider

Implements `AIProvider` using official OpenAI API (gpt-4o-mini or gpt-3.5-turbo) with JSON output mode.
"""

import json
import logging
from typing import Dict, Any
from openai import AsyncOpenAI

from app.ai.base import AIProvider
from app.core.config import settings
from app.schemas.resume import ParsedResumeData

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """
    OpenAI implementation for resume parsing and match explanations.
    """

    def __init__(self, api_key: str = ""):
        self.key = api_key or settings.OPENAI_API_KEY
        self.client = AsyncOpenAI(api_key=self.key) if self.key else None

    @property
    def provider_name(self) -> str:
        return "openai"

    async def parse_resume(self, raw_text: str) -> ParsedResumeData:
        """
        Parses resume text into structured JSON using OpenAI Chat Completions API with response_format json_object.
        """
        if not self.client:
            raise ValueError("OpenAI API key is missing. Set OPENAI_API_KEY in .env.")

        prompt = (
            "You are an expert resume parser. Extract structured information from the resume text provided below.\n"
            "Respond ONLY with a JSON object containing the following keys:\n"
            "- full_name: string or null\n"
            "- email: string or null\n"
            "- phone: string or null\n"
            "- skills: list of strings (technical and soft skills)\n"
            "- experience: list of objects with keys: title, company, duration, description\n"
            "- education: list of objects with keys: degree, institution, year\n"
            "- projects: list of objects with keys: title, description, technologies\n\n"
            f"Resume Text:\n{raw_text[:4000]}"
        )

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional resume parser returning valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )

            content = response.choices[0].message.content or "{}"
            parsed_json = json.loads(content)
            return ParsedResumeData.model_validate(parsed_json)

        except Exception as exc:
            logger.error(f"OpenAI resume parsing error: {exc}")
            raise RuntimeError(f"OpenAI parsing failed: {exc}")

    async def explain_match(
        self,
        resume_data: Dict[str, Any],
        job_title: str,
        company: str,
        job_description: str,
        score: float
    ) -> Dict[str, Any]:
        """
        Generates structured match explanation text using OpenAI.
        """
        if not self.client:
            raise ValueError("OpenAI API key is missing.")

        prompt = (
            f"Analyze the match between a candidate's resume and a job listing.\n"
            f"Candidate Skills: {resume_data.get('skills', [])}\n"
            f"Job: {job_title} at {company}\n"
            f"Job Description: {job_description[:2000]}\n"
            f"Calculated Score: {score}%\n\n"
            "Return JSON with:\n"
            "- reasons: list of strings explaining why it's a good match (matching skills, experience)\n"
            "- missing_skills: list of strings of skills required by job but missing from candidate\n"
            "- recommendation: single sentence summary (e.g. 'Strong Match — candidate possesses key Python & REST API skills.')"
        )

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You analyze job candidate fit and return concise JSON explanations."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )

            content = response.choices[0].message.content or "{}"
            return json.loads(content)

        except Exception as exc:
            logger.error(f"OpenAI match explanation error: {exc}")
            return {
                "reasons": ["Matching skills identified"],
                "missing_skills": [],
                "recommendation": "Calculated fit score based on skills overlap."
            }

    async def analyze_resume_quality(
        self,
        raw_text: str,
        parsed_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyzes general resume quality using OpenAI or fallback rules.
        """
        from app.ai.mock_provider import MockProvider
        mock = MockProvider()
        return await mock.analyze_resume_quality(raw_text, parsed_data)

    async def suggest_job_specific_improvements(
        self,
        raw_text: str,
        parsed_data: Dict[str, Any],
        job_title: str,
        job_description: str
    ) -> Dict[str, Any]:
        """
        Provides tailored recommendations to customize resume for a target job posting using OpenAI or fallback rules.
        """
        from app.ai.mock_provider import MockProvider
        mock = MockProvider()
        return await mock.suggest_job_specific_improvements(raw_text, parsed_data, job_title, job_description)
