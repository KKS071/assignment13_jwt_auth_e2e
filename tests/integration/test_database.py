# File: tests/integration/test_database.py
# Purpose: Tests for database module (engine, sessionmaker, Base)

import sys
import importlib
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base

DATABASE_MODULE = "app.database"


@pytest.fixture
def mock_settings(monkeypatch):
    mock_url = "postgresql://user:password@localhost:5432/test_db"
    mock_s = MagicMock()
    mock_s.DATABASE_URL = mock_url
    if DATABASE_MODULE in sys.modules:
        del sys.modules[DATABASE_MODULE]
    monkeypatch.setattr(f"{DATABASE_MODULE}.settings", mock_s)
    return mock_s


def reload_db():
    if DATABASE_MODULE in sys.modules:
        del sys.modules[DATABASE_MODULE]
    return importlib.import_module(DATABASE_MODULE)


def test_base_declaration(mock_settings):
    db = reload_db()
    assert isinstance(db.Base, declarative_base().__class__)


def test_get_engine_success(mock_settings):
    db = reload_db()
    assert isinstance(db.get_engine(), Engine)


def test_get_engine_failure(mock_settings):
    db = reload_db()
    with patch("app.database.create_engine", side_effect=SQLAlchemyError("fail")):
        with pytest.raises(SQLAlchemyError, match="fail"):
            db.get_engine()


def test_get_sessionmaker(mock_settings):
    db = reload_db()
    engine = db.get_engine()
    assert isinstance(db.get_sessionmaker(engine), sessionmaker)
