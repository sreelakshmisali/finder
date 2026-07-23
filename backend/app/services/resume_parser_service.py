"""
Resume Parser Service

Extracts plain text from PDF resume files using `pdfplumber` and processes it
through the configured `AIProvider` to generate structured JSON.
"""

import os
import logging
import uuid
import pdfplumber
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import get_ai_provider
from app.repositories.resume_repository import ResumeRepository
from app.schemas.resume import ResumeResponse

logger = logging.getLogger(__name__)


class ResumeParserService:
    """
    Service for extracting text from PDF resumes and parsing structured fields.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ResumeRepository(db)
        self.ai = get_ai_provider()

    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extracts plain text from a PDF file using pdfplumber.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Resume file not found at path: {file_path}")

        extracted_text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"

        return extracted_text.strip()

    async def parse_resume(self, resume_id: uuid.UUID, user_id: uuid.UUID) -> Optional[ResumeResponse]:
        """
        Extracts text from PDF file, sends text to AI parser, and saves parsed JSON to DB.
        """
        db_resume = await self.repo.get_by_id(resume_id, user_id)
        if not db_resume:
            return None

        # 1. Extract text from PDF file
        raw_text = self.extract_text_from_pdf(db_resume.file_path)

        # 2. Parse structured fields using AI provider
        parsed_model = await self.ai.parse_resume(raw_text)
        parsed_dict = parsed_model.model_dump()

        # 3. Save to database
        updated_resume = await self.repo.update_parsed_data(
            resume_id=resume_id,
            user_id=user_id,
            raw_text=raw_text,
            parsed_data=parsed_dict
        )

        if not updated_resume:
            return None

        return ResumeResponse.model_validate(updated_resume)
