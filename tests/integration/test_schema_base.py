# File: tests/integration/test_schema_base.py
# Purpose: Tests for base Pydantic schemas in app/schemas/base.py

import pytest
from pydantic import ValidationError
from app.schemas.base import UserBase, PasswordMixin, UserCreate, UserLogin


def test_user_base_valid():
    u = UserBase(first_name="John", last_name="Doe", email="john@example.com", username="johndoe")
    assert u.first_name == "John"
    assert u.email == "john@example.com"


def test_user_base_invalid_email():
    with pytest.raises(ValidationError):
        UserBase(first_name="J", last_name="D", email="not-an-email", username="jd123")


def test_password_mixin_valid():
    m = PasswordMixin(password="SecurePass123")
    assert m.password == "SecurePass123"


def test_password_mixin_too_short():
    with pytest.raises(ValidationError):
        PasswordMixin(password="Sh0rt")


def test_password_mixin_no_uppercase():
    with pytest.raises(ValidationError, match="uppercase"):
        PasswordMixin(password="lowercase123")


def test_password_mixin_no_lowercase():
    with pytest.raises(ValidationError, match="lowercase"):
        PasswordMixin(password="UPPERCASE123")


def test_password_mixin_no_digit():
    with pytest.raises(ValidationError, match="digit"):
        PasswordMixin(password="NoDigitsHere")


def test_user_create_valid():
    u = UserCreate(
        first_name="John", last_name="Doe", email="john@example.com",
        username="johndoe", password="SecurePass123",
    )
    assert u.username == "johndoe"


def test_user_create_bad_password():
    with pytest.raises(ValidationError):
        UserCreate(
            first_name="John", last_name="Doe", email="john@example.com",
            username="johndoe", password="short",
        )


def test_user_login_valid():
    u = UserLogin(username="johndoe", password="SecurePass123")
    assert u.username == "johndoe"


def test_user_login_short_username():
    with pytest.raises(ValidationError):
        UserLogin(username="jd", password="SecurePass123")


def test_user_login_short_password():
    with pytest.raises(ValidationError):
        UserLogin(username="johndoe", password="short")
