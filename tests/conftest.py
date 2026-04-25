# File: tests/conftest.py
# Purpose: Shared fixtures for all tests (DB, server, Playwright)

import socket
import subprocess
import time
import logging
from contextlib import contextmanager
from typing import Generator, Dict, List

import pytest
import requests
from faker import Faker
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from playwright.sync_api import sync_playwright, Browser

from app.database import Base, get_engine, get_sessionmaker
from app.models.user import User
from app.core.config import settings
from app.database_init import init_db, drop_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

fake = Faker()
Faker.seed(12345)

test_engine = get_engine(database_url=settings.DATABASE_URL)
TestingSessionLocal = get_sessionmaker(engine=test_engine)


# ── Helpers ────────────────────────────────────────────────────────────────

def create_fake_user() -> Dict[str, str]:
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.unique.email(),
        "username": fake.unique.user_name(),
        "password": fake.password(length=12),
    }


@contextmanager
def managed_db_session():
    session = TestingSessionLocal()
    try:
        yield session
    except SQLAlchemyError as e:
        logger.error(f"DB error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def wait_for_server(url: str, timeout: int = 30) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            if requests.get(url).status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    return False


class ServerStartupError(Exception):
    pass


# ── DB Fixtures ────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    logger.info("Setting up test database...")
    try:
        Base.metadata.drop_all(bind=test_engine)
        Base.metadata.create_all(bind=test_engine)
        init_db()
    except Exception as e:
        logger.error(f"DB setup failed: {e}")
        raise
    yield
    logger.info("Tearing down test database...")
    drop_db()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture
def fake_user_data() -> Dict[str, str]:
    return create_fake_user()


@pytest.fixture
def test_user(db_session: Session) -> User:
    data = create_fake_user()
    user = User(**data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def seed_users(db_session: Session, request) -> List[User]:
    n = getattr(request, "param", 5)
    users = [User(**create_fake_user()) for _ in range(n)]
    db_session.add_all(users)
    db_session.commit()
    return users


# ── Server Fixture ─────────────────────────────────────────────────────────

def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def fastapi_server():
    port = 8000
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", port)) == 0:
            port = _find_free_port()

    proc = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    health = f"http://127.0.0.1:{port}/health"
    if not wait_for_server(health, timeout=30):
        proc.terminate()
        raise ServerStartupError(f"Server did not start at {health}")

    base_url = f"http://127.0.0.1:{port}/"
    logger.info(f"Test server running at {base_url}")
    yield base_url

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


# ── Playwright Fixtures ────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def browser_context():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        yield browser
        browser.close()


@pytest.fixture
def page(browser_context: Browser):
    ctx = browser_context.new_context(viewport={"width": 1280, "height": 720}, ignore_https_errors=True)
    pg = ctx.new_page()
    yield pg
    pg.close()
    ctx.close()


# ── CLI Options ────────────────────────────────────────────────────────────

def pytest_addoption(parser):
    parser.addoption("--preserve-db", action="store_true", default=False, help="Keep DB after tests")
    parser.addoption("--run-slow", action="store_true", default=False, help="Run slow tests")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="use --run-slow to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
