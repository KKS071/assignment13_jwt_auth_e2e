# File: tests/e2e/test_fastapi_calculator.py
# Purpose: Playwright E2E tests for calculator functionality

import uuid
import pytest


# ── Helpers ────────────────────────────────────────────────────────────────

def unique_user():
    uid = uuid.uuid4().hex[:8]
    return {
        "first_name": "Test",
        "last_name": "User",
        "username": f"user_{uid}",
        "email": f"user_{uid}@example.com",
        "password": "TestPass1!",
        "confirm_password": "TestPass1!",
    }


def fill_register_form(page, u):
    page.fill("#first_name", u["first_name"])
    page.fill("#last_name", u["last_name"])
    page.fill("#username", u["username"])
    page.fill("#email", u["email"])
    page.fill("#password", u["password"])
    page.fill("#confirm_password", u["confirm_password"])


def fill_login_form(page, username, password):
    page.fill("#username", username)
    page.fill("#password", password)


# ── Positive tests ─────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_register_valid_user(page, fastapi_server):
    """Registering with valid credentials shows a success message."""
    page.goto(f"{fastapi_server}register")
    u = unique_user()
    fill_register_form(page, u)
    page.click("button[type=submit]")
    page.wait_for_selector("#successAlert:not(.hidden)", timeout=5000)
    assert page.is_visible("#successAlert")


@pytest.mark.e2e
def test_login_valid_user(page, fastapi_server):
    """Logging in with correct credentials stores a token and redirects."""
    # First register via API so the user definitely exists
    import requests
    u = unique_user()
    resp = requests.post(
        f"{fastapi_server}auth/register",
        json={
            "first_name": u["first_name"],
            "last_name": u["last_name"],
            "username": u["username"],
            "email": u["email"],
            "password": u["password"],
            "confirm_password": u["confirm_password"],
        },
    )
    assert resp.status_code == 201, resp.text

    page.goto(f"{fastapi_server}login")
    fill_login_form(page, u["username"], u["password"])
    page.click("button[type=submit]")
    # Either redirects to dashboard or shows a success message
    page.wait_for_url(f"{fastapi_server}dashboard", timeout=5000)
    assert "dashboard" in page.url


# ── Negative tests ─────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_register_short_password(page, fastapi_server):
    """Registering with a short password shows a client-side error."""
    page.goto(f"{fastapi_server}register")
    u = unique_user()
    u["password"] = "Ab1!"
    u["confirm_password"] = "Ab1!"
    fill_register_form(page, u)
    page.click("button[type=submit]")
    page.wait_for_selector("#errorAlert:not(.hidden)", timeout=5000)
    assert page.is_visible("#errorAlert")


@pytest.mark.e2e
def test_register_invalid_email(page, fastapi_server):
    """Registering with a bad email format shows a client-side error."""
    page.goto(f"{fastapi_server}register")
    u = unique_user()
    u["email"] = "not-an-email"
    fill_register_form(page, u)
    page.click("button[type=submit]")
    page.wait_for_selector("#errorAlert:not(.hidden)", timeout=5000)
    assert page.is_visible("#errorAlert")


@pytest.mark.e2e
def test_login_wrong_password(page, fastapi_server):
    """Logging in with the wrong password shows an error message."""
    import requests
    u = unique_user()
    requests.post(
        f"{fastapi_server}auth/register",
        json={
            "first_name": u["first_name"],
            "last_name": u["last_name"],
            "username": u["username"],
            "email": u["email"],
            "password": u["password"],
            "confirm_password": u["confirm_password"],
        },
    )

    page.goto(f"{fastapi_server}login")
    fill_login_form(page, u["username"], "WrongPass99!")
    page.click("button[type=submit]")
    page.wait_for_selector("#errorAlert:not(.hidden)", timeout=5000)
    assert page.is_visible("#errorAlert")
