# File: tests/integration/test_api.py
# Purpose: FastAPI endpoint integration tests using TestClient

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.core.config import settings

# Use an in-memory SQLite DB for speed (no Postgres needed for endpoint tests)
TEST_DB_URL = settings.DATABASE_URL  # uses the same PG DB seeded by conftest

engine = create_engine(TEST_DB_URL)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def make_user():
    uid = uuid.uuid4().hex[:8]
    return {
        "first_name": "Test",
        "last_name": "User",
        "username": f"api_{uid}",
        "email": f"api_{uid}@test.com",
        "password": "TestPass1!",
        "confirm_password": "TestPass1!",
    }


# ── Pages ──────────────────────────────────────────────────────────────────

def test_home_page():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_login_page():
    resp = client.get("/login")
    assert resp.status_code == 200


def test_register_page():
    resp = client.get("/register")
    assert resp.status_code == 200


def test_dashboard_page():
    resp = client.get("/dashboard")
    assert resp.status_code == 200


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── Auth endpoints ─────────────────────────────────────────────────────────

def test_register_success():
    resp = client.post("/auth/register", json=make_user())
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"].startswith("api_")
    assert "id" in data


def test_register_duplicate():
    u = make_user()
    client.post("/auth/register", json=u)
    resp = client.post("/auth/register", json=u)
    assert resp.status_code == 400
    assert "already exists" in resp.json()["detail"]


def test_register_invalid_schema():
    resp = client.post("/auth/register", json={"email": "bad"})
    assert resp.status_code == 422


def test_login_success():
    u = make_user()
    client.post("/auth/register", json=u)
    resp = client.post("/auth/login", json={"username": u["username"], "password": u["password"]})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    u = make_user()
    client.post("/auth/register", json=u)
    resp = client.post("/auth/login", json={"username": u["username"], "password": "WrongPass99!"})
    assert resp.status_code == 401


def test_login_unknown_user():
    resp = client.post("/auth/login", json={"username": "nobody_xyz", "password": "TestPass1!"})
    assert resp.status_code == 401


def test_form_token_login():
    u = make_user()
    client.post("/auth/register", json=u)
    resp = client.post("/auth/token", data={"username": u["username"], "password": u["password"]})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_form_token_login_bad():
    resp = client.post("/auth/token", data={"username": "nobody_xyz", "password": "TestPass1!"})
    assert resp.status_code == 401


# ── Calculations (auth-protected) ─────────────────────────────────────────

def _get_token():
    u = make_user()
    client.post("/auth/register", json=u)
    resp = client.post("/auth/login", json={"username": u["username"], "password": u["password"]})
    return resp.json()["access_token"]


def test_create_calculation_addition():
    token = _get_token()
    resp = client.post(
        "/calculations",
        json={"type": "addition", "inputs": [1, 2, 3]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["result"] == 6.0


def test_create_calculation_subtraction():
    token = _get_token()
    resp = client.post(
        "/calculations",
        json={"type": "subtraction", "inputs": [10, 3, 2]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["result"] == 5.0


def test_create_calculation_multiplication():
    token = _get_token()
    resp = client.post(
        "/calculations",
        json={"type": "multiplication", "inputs": [2, 3, 4]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["result"] == 24.0


def test_create_calculation_division():
    token = _get_token()
    resp = client.post(
        "/calculations",
        json={"type": "division", "inputs": [100, 5, 2]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["result"] == 10.0


def test_create_calculation_divide_by_zero():
    token = _get_token()
    resp = client.post(
        "/calculations",
        json={"type": "division", "inputs": [10, 0]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422  # caught by Pydantic validator


def test_list_calculations():
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/calculations", json={"type": "addition", "inputs": [1, 2]}, headers=headers)
    resp = client.get("/calculations", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_get_calculation_by_id():
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post("/calculations", json={"type": "addition", "inputs": [5, 5]}, headers=headers).json()
    resp = client.get(f"/calculations/{created['id']}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["result"] == 10.0


def test_get_calculation_bad_id():
    token = _get_token()
    resp = client.get("/calculations/not-a-uuid", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400


def test_get_calculation_not_found():
    token = _get_token()
    resp = client.get(f"/calculations/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


def test_update_calculation():
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}"}
    calc = client.post("/calculations", json={"type": "addition", "inputs": [1, 2]}, headers=headers).json()
    resp = client.put(f"/calculations/{calc['id']}", json={"inputs": [10, 20]}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["result"] == 30.0


def test_update_calculation_bad_id():
    token = _get_token()
    resp = client.put("/calculations/bad-id", json={"inputs": [1, 2]}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400


def test_update_calculation_not_found():
    token = _get_token()
    resp = client.put(
        f"/calculations/{uuid.uuid4()}",
        json={"inputs": [1, 2]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


def test_delete_calculation():
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}"}
    calc = client.post("/calculations", json={"type": "addition", "inputs": [1, 2]}, headers=headers).json()
    resp = client.delete(f"/calculations/{calc['id']}", headers=headers)
    assert resp.status_code == 204


def test_delete_calculation_bad_id():
    token = _get_token()
    resp = client.delete("/calculations/bad-id", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400


def test_delete_calculation_not_found():
    token = _get_token()
    resp = client.delete(f"/calculations/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


def test_unauthenticated_calculations():
    resp = client.get("/calculations")
    assert resp.status_code == 401

    resp = client.post("/calculations", json={"type": "addition", "inputs": [1, 2]})
    assert resp.status_code == 401
