"""
Auth Service

Business logic layer for user registration, login credential verification, and JWT issuance.
"""

import logging
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password, create_access_token
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse

logger = logging.getLogger(__name__)


class AuthService:
    """
    Business logic layer for authentication operations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepository(db)

    async def register_user(self, payload: UserCreate) -> TokenResponse:
        """
        Registers a new user account and returns an access token.
        """
        existing = await self.repo.get_by_email(payload.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email '{payload.email}' already exists."
            )

        user = await self.repo.create(
            email=payload.email,
            full_name=payload.full_name,
            password=payload.password
        )

        token = create_access_token(subject=str(user.id))
        user_resp = UserResponse.model_validate(user)

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=user_resp
        )

    async def login_user(self, payload: UserLogin) -> TokenResponse:
        """
        Authenticates user credentials and returns an access token.
        """
        user = await self.repo.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password."
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated."
            )

        token = create_access_token(subject=str(user.id))
        user_resp = UserResponse.model_validate(user)

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=user_resp
        )
