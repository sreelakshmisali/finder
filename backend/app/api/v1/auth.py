"""
Auth API Endpoints

Provides REST routes for user registration, login, and current profile fetching.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import decode_access_token
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Dependency helper retrieving current user from Bearer JWT token.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing."
        )

    user_id_str = decode_access_token(token)
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token."
        )

    repo = UserRepository(db)
    user = await repo.get_by_email(user_id_str)
    if not user:
        try:
            import uuid
            user = await repo.get_by_id(uuid.UUID(user_id_str))
        except ValueError:
            pass

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found."
        )

    return UserResponse.model_validate(user)


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
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """
    Current user endpoint.
    """
    return current_user
