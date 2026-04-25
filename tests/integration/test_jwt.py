# File: tests/integration/test_jwt.py
# Purpose: Unit tests for JWT utility functions

import pytest
from datetime import timedelta
from uuid import uuid4

from app.auth.jwt import (
    get_password_hash,
    verify_password,
    create_token,
    decode_token,
)
from app.schemas.token import TokenType


def test_hash_and_verify_password():
    pw = "MySecurePass123"
    hashed = get_password_hash(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPass", hashed) is False


def test_create_and_decode_access_token():
    uid = str(uuid4())
    token = create_token(uid, TokenType.ACCESS)
    payload = decode_token(token, TokenType.ACCESS)
    assert payload is not None
    assert payload["sub"] == uid
    assert payload["type"] == "access"


def test_create_and_decode_refresh_token():
    uid = str(uuid4())
    token = create_token(uid, TokenType.REFRESH)
    payload = decode_token(token, TokenType.REFRESH)
    assert payload is not None
    assert payload["sub"] == uid
    assert payload["type"] == "refresh"


def test_access_token_rejected_as_refresh():
    uid = str(uuid4())
    token = create_token(uid, TokenType.ACCESS)
    result = decode_token(token, TokenType.REFRESH)
    assert result is None


def test_refresh_token_rejected_as_access():
    uid = str(uuid4())
    token = create_token(uid, TokenType.REFRESH)
    result = decode_token(token, TokenType.ACCESS)
    assert result is None


def test_invalid_token_returns_none():
    assert decode_token("not.a.real.token", TokenType.ACCESS) is None


def test_create_token_with_uuid():
    uid = uuid4()
    token = create_token(uid, TokenType.ACCESS)
    payload = decode_token(token, TokenType.ACCESS)
    assert payload is not None
    assert payload["sub"] == str(uid)


def test_expired_token_returns_none():
    uid = str(uuid4())
    token = create_token(uid, TokenType.ACCESS, expires_delta=timedelta(seconds=-1))
    result = decode_token(token, TokenType.ACCESS)
    assert result is None


def test_token_has_jti():
    uid = str(uuid4())
    token = create_token(uid, TokenType.ACCESS)
    payload = decode_token(token, TokenType.ACCESS)
    assert "jti" in payload
    # Each token should have a unique jti
    token2 = create_token(uid, TokenType.ACCESS)
    payload2 = decode_token(token2, TokenType.ACCESS)
    assert payload["jti"] != payload2["jti"]
