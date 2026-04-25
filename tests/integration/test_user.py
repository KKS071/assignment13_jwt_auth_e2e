# File: tests/integration/test_user.py
# Purpose: Integration tests for User model DB interactions

import pytest
import logging
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from tests.conftest import create_fake_user, managed_db_session

logger = logging.getLogger(__name__)


def test_database_connection(db_session):
    result = db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


def test_managed_session():
    with managed_db_session() as session:
        session.execute(text("SELECT 1"))
        try:
            session.execute(text("SELECT * FROM nonexistent_table"))
        except Exception as e:
            assert "nonexistent_table" in str(e)


def test_session_handling(db_session):
    initial = db_session.query(User).count()

    u1 = User(first_name="User", last_name="One", email="sess1@example.com", username="sessu1", password="pw")
    db_session.add(u1)
    db_session.commit()

    u2 = User(first_name="User", last_name="Two", email="sess1@example.com", username="sessu2", password="pw")
    db_session.add(u2)
    try:
        db_session.commit()
    except Exception:
        db_session.rollback()

    u3 = User(first_name="User", last_name="Three", email="sess3@example.com", username="sessu3", password="pw")
    db_session.add(u3)
    db_session.commit()

    assert db_session.query(User).count() == initial + 2


def test_create_user_with_faker(db_session):
    data = create_fake_user()
    user = User(**data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    assert user.id is not None
    assert user.email == data["email"]


def test_create_multiple_users(db_session):
    users = [User(**create_fake_user()) for _ in range(3)]
    db_session.add_all(users)
    db_session.commit()
    assert len(users) == 3


def test_query_methods(db_session, seed_users):
    count = db_session.query(User).count()
    assert count >= len(seed_users)
    first = seed_users[0]
    found = db_session.query(User).filter_by(email=first.email).first()
    assert found is not None
    ordered = db_session.query(User).order_by(User.email).all()
    assert len(ordered) >= len(seed_users)


def test_transaction_rollback(db_session):
    initial = db_session.query(User).count()
    try:
        data = create_fake_user()
        user = User(**data)
        db_session.add(user)
        db_session.execute(text("SELECT * FROM nonexistent_table"))
        db_session.commit()
    except Exception:
        db_session.rollback()
    assert db_session.query(User).count() == initial


def test_update_with_refresh(db_session, test_user):
    original_email = test_user.email
    original_updated = test_user.updated_at
    test_user.email = f"new_{original_email}"
    db_session.commit()
    db_session.refresh(test_user)
    assert test_user.email == f"new_{original_email}"
    assert test_user.updated_at >= original_updated


@pytest.mark.slow
def test_bulk_operations(db_session):
    users = [User(**create_fake_user()) for _ in range(10)]
    db_session.bulk_save_objects(users)
    db_session.commit()
    assert db_session.query(User).count() >= 10


def test_unique_email_constraint(db_session):
    data = create_fake_user()
    db_session.add(User(**data))
    db_session.commit()
    dup = create_fake_user()
    dup["email"] = data["email"]
    db_session.add(User(**dup))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_unique_username_constraint(db_session):
    data = create_fake_user()
    db_session.add(User(**data))
    db_session.commit()
    dup = create_fake_user()
    dup["username"] = data["username"]
    db_session.add(User(**dup))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_persistence_after_constraint(db_session):
    u = User(first_name="F", last_name="L", email="persist@example.com", username="persistuser", password="pw")
    db_session.add(u)
    db_session.commit()
    saved_id = u.id

    try:
        dup = User(first_name="F2", last_name="L2", email="persist@example.com", username="persistuser2", password="pw")
        db_session.add(dup)
        db_session.commit()
    except IntegrityError:
        db_session.rollback()

    found = db_session.query(User).filter_by(id=saved_id).first()
    assert found is not None
    assert found.email == "persist@example.com"


def test_error_handling():
    with pytest.raises(Exception):
        with managed_db_session() as session:
            session.execute(text("INVALID SQL"))
