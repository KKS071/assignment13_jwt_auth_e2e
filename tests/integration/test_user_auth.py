# File: tests/integration/test_user_auth.py
# Purpose: Integration tests for User model auth methods

import pytest
from app.models.user import User


def test_password_hashing(db_session, fake_user_data):
    pw = "TestPass123"
    hashed = User.hash_password(pw)
    user = User(
        first_name=fake_user_data["first_name"],
        last_name=fake_user_data["last_name"],
        email=fake_user_data["email"],
        username=fake_user_data["username"],
        password=hashed,
    )
    assert user.verify_password(pw) is True
    assert user.verify_password("WrongPass") is False
    assert hashed != pw


def test_user_registration(db_session, fake_user_data):
    fake_user_data["password"] = "TestPass123"
    user = User.register(db_session, fake_user_data)
    db_session.commit()
    assert user.first_name == fake_user_data["first_name"]
    assert user.is_active is True
    assert user.is_verified is False
    assert user.verify_password("TestPass123") is True


def test_duplicate_registration(db_session):
    data1 = {"first_name": "A", "last_name": "B", "email": "dup@example.com", "username": "dupuser1", "password": "TestPass123"}
    data2 = {"first_name": "C", "last_name": "D", "email": "dup@example.com", "username": "dupuser2", "password": "TestPass123"}
    User.register(db_session, data1)
    db_session.commit()
    with pytest.raises(ValueError, match="Username or email already exists"):
        User.register(db_session, data2)


def test_authenticate_success(db_session, fake_user_data):
    fake_user_data["password"] = "TestPass123"
    User.register(db_session, fake_user_data)
    db_session.commit()
    result = User.authenticate(db_session, fake_user_data["username"], "TestPass123")
    assert result is not None
    assert "access_token" in result
    assert result["token_type"] == "bearer"
    assert "user" in result


def test_authenticate_with_email(db_session, fake_user_data):
    fake_user_data["password"] = "TestPass123"
    User.register(db_session, fake_user_data)
    db_session.commit()
    result = User.authenticate(db_session, fake_user_data["email"], "TestPass123")
    assert result is not None


def test_authenticate_wrong_password(db_session, fake_user_data):
    fake_user_data["password"] = "TestPass123"
    User.register(db_session, fake_user_data)
    db_session.commit()
    result = User.authenticate(db_session, fake_user_data["username"], "WrongPass123")
    assert result is None


def test_last_login_updated(db_session, fake_user_data):
    fake_user_data["password"] = "TestPass123"
    user = User.register(db_session, fake_user_data)
    db_session.commit()
    assert user.last_login is None
    User.authenticate(db_session, fake_user_data["username"], "TestPass123")
    db_session.refresh(user)
    assert user.last_login is not None


def test_short_password_rejected(db_session):
    data = {"first_name": "X", "last_name": "Y", "email": "short@example.com", "username": "shortpw", "password": "Ab1"}
    with pytest.raises(ValueError, match="Password must be at least 6 characters"):
        User.register(db_session, data)


def test_missing_password_rejected(db_session):
    data = {"first_name": "X", "last_name": "Y", "email": "nopw@example.com", "username": "nopwuser"}
    with pytest.raises(ValueError, match="Password must be at least 6 characters"):
        User.register(db_session, data)


def test_invalid_token():
    assert User.verify_token("invalid.token.string") is None


def test_token_create_and_verify(db_session, fake_user_data):
    fake_user_data["password"] = "TestPass123"
    user = User.register(db_session, fake_user_data)
    db_session.commit()
    token = User.create_access_token({"sub": str(user.id)})
    result = User.verify_token(token)
    assert result == user.id


def test_user_str(test_user):
    assert str(test_user) == f"<User(name={test_user.first_name} {test_user.last_name}, email={test_user.email})>"


def test_unique_email_constraint(db_session):
    d1 = {"first_name": "U", "last_name": "N", "email": "uni@example.com", "username": "uniuser1", "password": "TestPass123"}
    d2 = {"first_name": "U", "last_name": "N", "email": "uni@example.com", "username": "uniuser2", "password": "TestPass123"}
    User.register(db_session, d1)
    db_session.commit()
    with pytest.raises(ValueError):
        User.register(db_session, d2)
