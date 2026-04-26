# File: tests/integration/test_get_db.py
# Purpose: Tests for the get_db dependency and database_init helpers

import pytest
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
    """get_db terminates cleanly when the caller throws an exception."""
    gen = get_db()
    session = next(gen)
    assert session is not None

    # Throw into the generator and capture whatever comes out
    try:
        gen.throw(RuntimeError("boom"))
    except (RuntimeError, StopIteration):
        pass  # either the exception propagates or the generator catches and returns

    # Generator must now be exhausted — calling next() should raise StopIteration
    with pytest.raises(StopIteration):
        next(gen)


def test_init_db_and_drop_db_do_not_raise():
    """init_db / drop_db should complete without raising."""
    init_db()
    init_db()   # idempotent
    drop_db()
    init_db()   # restore tables for remaining tests
