"""
Auth API Endpoints

Provides REST routes for user registration, login, and current profile fetching.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user account",
    description="Registers a new user profile and returns a JWT access token."
)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register endpoint.
    """
    service = AuthService(db)
    return await service.register_user(payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in user",
    description="Verifies user credentials and returns a JWT access token."
)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Login endpoint.
    """
    service = AuthService(db)
    return await service.login_user(payload)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns profile details for the currently authenticated user."
)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Current user endpoint.
    """
    return UserResponse.model_validate(current_user)
