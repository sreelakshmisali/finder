"""
Automation Base Interface

Abstract base class defining the contract for Playwright ATS form automators
(Greenhouse, Lever, Ashby).

Safety Contract:
- The automator navigates to the job URL, uploads the PDF resume, and fills candidate details.
- If unhandled custom questions exist, it surfaces them to the UI (`awaiting_input`).
- It NEVER clicks the final "Submit Application" button automatically.
- It stops at `awaiting_confirmation` until explicit user approval is received.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class AutomationQuestion(BaseModel):
    """
    Represents an unhandled custom question detected on the application form.
    """
    id: str = Field(..., description="Field selector or input name")
    label: str = Field(..., description="Human-readable label or question text")
    field_type: str = Field("text", description="Field type: 'text', 'select', 'checkbox'")
    required: bool = Field(False, description="Whether question is mandatory")
    options: Optional[List[str]] = Field(None, description="Select options if dropdown")
    value: Optional[str] = Field(None, description="User provided answer")


class AutomationStepResult(BaseModel):
    """
    Result state payload from an automation step.
    """
    status: str = Field(..., description="Status string: 'awaiting_input', 'awaiting_confirmation', 'completed', 'failed'")
    step_summary: str = Field(..., description="Summary message of completed actions")
    custom_questions: List[AutomationQuestion] = Field(default=[], description="Unfilled questions requiring user input")
    filled_fields_summary: List[str] = Field(default=[], description="List of fields filled (e.g. name, email, resume)")
    screenshot_path: Optional[str] = Field(None, description="Path to captured browser screenshot")


class ApplicationAutomator(ABC):
    """
    Abstract Base Class for ATS Form Automators.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Identifier name of ATS provider (e.g. 'greenhouse', 'lever', 'ashby').
        """
        pass

    @abstractmethod
    async def fill_form(
        self,
        job_url: str,
        resume_path: str,
        candidate_info: Dict[str, Any],
        answers: Optional[Dict[str, str]] = None
    ) -> AutomationStepResult:
        """
        Navigates to job URL, fills form fields, uploads PDF resume, and returns automation result.

        Args:
            job_url: Target application page URL.
            resume_path: Path to PDF resume file on disk.
            candidate_info: Candidate details (full_name, email, phone, etc.).
            answers: Optional answers dictionary provided by user for custom questions.

        Returns:
            `AutomationStepResult` with current status and any remaining custom questions.
        """
        pass

    @abstractmethod
    async def confirm_and_submit(
        self,
        job_url: str,
        resume_path: str,
        candidate_info: Dict[str, Any],
        answers: Dict[str, str]
    ) -> AutomationStepResult:
        """
        Executes the final submission after explicit user confirmation.
        """
        pass
