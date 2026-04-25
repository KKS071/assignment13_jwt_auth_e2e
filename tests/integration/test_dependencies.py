# File: tests/integration/test_dependencies.py
# Purpose: Tests for JWT auth dependency functions

import pytest
from unittest.mock import patch
from uuid import uuid4
from datetime import datetime, timezone
from fastapi import HTTPException, status

from app.auth.dependencies import get_current_user, get_current_active_user
from app.schemas.user import UserResponse
from app.models.user import User

_now = datetime.now(timezone.utc)

sample_user = {
    "id": uuid4(),
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "is_active": True,
    "is_verified": True,
    "created_at": _now,
    "updated_at": _now,
}

inactive_user = {
    "id": uuid4(),
    "username": "inactive",
    "email": "inactive@example.com",
    "first_name": "Inactive",
    "last_name": "User",
    "is_active": False,
    "is_verified": False,
    "created_at": _now,
    "updated_at": _now,
}


@pytest.fixture
def mock_verify():
    with patch.object(User, "verify_token") as m:
        yield m


def test_get_current_user_valid(mock_verify):
    mock_verify.return_value = sample_user
    result = get_current_user(token="valid")
    assert isinstance(result, UserResponse)
    assert result.username == "testuser"
    mock_verify.assert_called_once_with("valid")


def test_get_current_user_none_token(mock_verify):
    mock_verify.return_value = None
    with pytest.raises(HTTPException) as exc:
        get_current_user(token="bad")
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_empty_dict(mock_verify):
    mock_verify.return_value = {}
    with pytest.raises(HTTPException) as exc:
        get_current_user(token="bad")
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_sub_only(mock_verify):
    mock_verify.return_value = {"sub": str(uuid4())}
    result = get_current_user(token="valid")
    assert isinstance(result, UserResponse)
    assert result.username == "unknown"


def test_get_current_active_user_active(mock_verify):
    mock_verify.return_value = sample_user
    user = get_current_user(token="valid")
    active = get_current_active_user(current_user=user)
    assert active.is_active is True


def test_get_current_active_user_inactive(mock_verify):
    mock_verify.return_value = inactive_user
    user = get_current_user(token="valid")
    with pytest.raises(HTTPException) as exc:
        get_current_active_user(current_user=user)
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.value.detail == "Inactive user"
