"""
Automation Schemas

Pydantic models for starting automation, providing custom question answers, and confirming application submission.
"""

from typing import List, Optional, Dict
import uuid
from pydantic import BaseModel, Field


class AutomationStartRequest(BaseModel):
    """
    Payload to trigger Playwright automation for an application.
    """
    answers: Optional[Dict[str, str]] = Field(None, description="Optional custom question answers")


class AutomationConfirmSubmitRequest(BaseModel):
    """
    Payload for explicit user confirmation to submit the application.
    """
    answers: Optional[Dict[str, str]] = Field(default={}, description="Final confirmed question answers")


class AutomationStateResponse(BaseModel):
    """
    State response returned to UI during automation steps.
    """
    application_id: uuid.UUID
    status: str
    step_summary: str
    custom_questions: List[Dict[str, str]] = []
    filled_fields_summary: List[str] = []
