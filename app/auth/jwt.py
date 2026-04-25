# File: app/auth/jwt.py
# Purpose: Password hashing and JWT token creation/verification

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from uuid import UUID

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import get_settings
from app.schemas.token import TokenType

settings = get_settings()

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS,
)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_token(
    user_id: Union[str, UUID],
    token_type: TokenType,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Build and sign a JWT for the given user."""
    if isinstance(user_id, UUID):
        user_id = str(user_id)

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    elif token_type == TokenType.ACCESS:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": user_id,
        "type": token_type.value,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_hex(16),
    }

    secret = (
        settings.JWT_SECRET_KEY if token_type == TokenType.ACCESS else settings.JWT_REFRESH_SECRET_KEY
    )
    return jwt.encode(payload, secret, algorithm=settings.ALGORITHM)


def decode_token(token: str, token_type: TokenType) -> Optional[dict]:
    """Decode and validate a JWT. Returns payload dict or None."""
    secret = (
        settings.JWT_SECRET_KEY if token_type == TokenType.ACCESS else settings.JWT_REFRESH_SECRET_KEY
    )
    try:
        payload = jwt.decode(token, secret, algorithms=[settings.ALGORITHM])
        if payload.get("type") != token_type.value:
            return None
        return payload
    except JWTError:
        return None
