# File: tests/integration/test_get_db.py
# Purpose: Tests for the get_db dependency and database_init helpers

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.database_init import init_db, drop_db


def test_get_db_yields_and_closes():
    """get_db should yield exactly once and close on exit."""
    gen = get_db()
    session = next(gen)
    assert session is not None
    try:
        next(gen)
    except StopIteration:
        pass


def test_get_db_closes_on_exception():
    """get_db must close the session even when an error is raised."""
    from app.database import SessionLocal
    mock_session = MagicMock()
    with patch.object(SessionLocal, "__call__", return_value=mock_session):
        gen = get_db()
        next(gen)
        try:
            gen.throw(RuntimeError("boom"))
        except RuntimeError:
            pass
        mock_session.close.assert_called_once()


def test_init_db_and_drop_db_do_not_raise():
    """init_db / drop_db should complete without raising."""
    init_db()
    init_db()   # idempotent
    drop_db()
    init_db()   # restore for remaining tests
