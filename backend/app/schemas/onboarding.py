"""
Onboarding Schema Definitions

Defines Pydantic models for returning onboarding completion status and profile percentage metrics.
"""

from pydantic import BaseModel, Field


class OnboardingStatusResponse(BaseModel):
    """
    Onboarding Status Response Schema

    Returns step progress indicators for account creation, resume upload,
    resume analysis, preferences configuration, and overall profile completion.
    """
    account_created: bool = Field(True, description="Whether user account is active")
    resume_uploaded: bool = Field(..., description="Whether a PDF resume has been uploaded")
    resume_analyzed: bool = Field(..., description="Whether active resume has been analyzed by AI")
    preferences_configured: bool = Field(..., description="Whether search preferences are configured")
    has_active_resume: bool = Field(..., description="Whether user has an active PDF resume")
    has_preferences: bool = Field(..., description="Whether user has saved job search preferences")
    profile_completion_percentage: float = Field(..., description="Calculated profile completion score (0 to 100)")
