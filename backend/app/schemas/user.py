"""
User & Auth Schemas

Pydantic validation models for registration, login, token output, and user profile data.
"""

from datetime import datetime
import uuid
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator


class UserCreate(BaseModel):
    """
    User registration payload.
    """
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name")
    password: str = Field(..., min_length=6, max_length=100, description="Password string")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class UserLogin(BaseModel):
    """
    User login payload.
    """
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Password string")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class UserResponse(BaseModel):
    """
    User profile output.
    """
    id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """
    JWT authentication token response.
    """
    access_token: str = Field(..., description="Signed JWT bearer token")
    token_type: str = Field("bearer", description="Token type string")
    user: UserResponse = Field(..., description="Authenticated user profile")
