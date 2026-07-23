"""
Security & Authentication Utilities

Handles Argon2 / bcrypt password hashing & verification and JSON Web Token (JWT) creation & validation.
"""

from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

# Password Hashing Context (Argon2 primary, bcrypt fallback for legacy hashes)
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
JWT_ISSUER = "finder-api"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies plain text password against stored Argon2/bcrypt hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generates Argon2 hash from plain text password.
    """
    return pwd_context.hash(password)


def create_access_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a signed JWT access token.

    Args:
        subject: Unique identifier (user ID string).
        expires_delta: Optional custom expiration timedelta.

    Returns:
        Encoded JWT token string.
    """
    now = datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": now,
        "iss": JWT_ISSUER
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[str]:
    """
    Decodes and validates a JWT token, returning the subject ID string.
    Verifies signature, expiration, and issuer claim.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        issuer = payload.get("iss")
        if issuer and issuer != JWT_ISSUER:
            return None
        return payload.get("sub")
    except JWTError:
        return None
