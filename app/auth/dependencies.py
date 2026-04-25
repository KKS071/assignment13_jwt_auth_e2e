# File: app/auth/dependencies.py
# Purpose: FastAPI dependencies for protected routes

from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.models.user import User
from app.schemas.user import UserResponse

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponse:
    """Verify token and return a UserResponse (no DB lookup needed here)."""
    err = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = User.verify_token(token)
    if token_data is None:
        raise err

    try:
        if isinstance(token_data, dict):
            if "username" in token_data:
                return UserResponse(**token_data)
            elif "sub" in token_data:
                return UserResponse(
                    id=token_data["sub"],
                    username="unknown",
                    email="unknown@example.com",
                    first_name="Unknown",
                    last_name="User",
                    is_active=True,
                    is_verified=False,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            else:
                raise err
        elif isinstance(token_data, UUID):
            return UserResponse(
                id=token_data,
                username="unknown",
                email="unknown@example.com",
                first_name="Unknown",
                last_name="User",
                is_active=True,
                is_verified=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        else:
            raise err
    except HTTPException:
        raise
    except Exception:
        raise err


def get_current_active_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user
