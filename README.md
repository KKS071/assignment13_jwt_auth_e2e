# Assignment 13 – JWT Auth E2E

[![CI](https://github.com/KKS071/assignment13_jwt_auth_e2e/actions/workflows/ci.yml/badge.svg)](https://github.com/KKS071/assignment13_jwt_auth_e2e/actions)
[![Docker](https://img.shields.io/docker/v/kks59/601_module13?label=Docker%20Hub)](https://hub.docker.com/r/kks59/601_module13)

A FastAPI application with JWT authentication, PostgreSQL, Playwright E2E tests, and a full CI/CD pipeline.

- **GitHub:** https://github.com/KKS071/assignment13_jwt_auth_e2e
- **Docker Hub:** https://hub.docker.com/r/kks59/601_module13

---

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy, psycopg2, python-jose, passlib/bcrypt
- **Frontend:** Jinja2 templates, vanilla JS
- **Tests:** pytest, pytest-cov, Playwright (all suites run in one pass)
- **CI/CD:** GitHub Actions (test → security scan → Docker push)
- **Containers:** Docker, Docker Compose, pgAdmin

---

## Project Structure

```
assignment13_jwt_auth_e2e/
├── app/
│   ├── auth/
│   │   ├── dependencies.py       # FastAPI auth dependencies
│   │   └── jwt.py                # Token creation/verification
│   ├── core/
│   │   ├── config.py             # Settings via pydantic-settings
│   │   ├── dependencies.py       # Core dependencies
│   │   ├── jwt.py                # Core JWT utilities
│   │   └── redis.py              # Redis client setup
│   ├── models/
│   │   ├── calculation.py        # Polymorphic calculation ORM model
│   │   └── user.py               # User ORM model with auth methods
│   ├── schemas/
│   │   ├── base.py               # Shared base schemas
│   │   ├── calculation.py        # Calculation request/response schemas
│   │   ├── token.py              # JWT token schemas
│   │   └── user.py               # User request/response schemas
│   ├── operations/
│   │   └── __init__.py           # Arithmetic helper functions
│   ├── database.py               # Engine, session, get_db dependency
│   ├── database_init.py          # init_db / drop_db with CASCADE support
│   └── main.py                   # FastAPI app + all routes
├── templates/
│   ├── layout.html
│   ├── index.html
│   ├── register.html             # Client-side validation + success/error alerts
│   ├── login.html                # JWT stored in localStorage on success
│   └── dashboard.html            # Calculations UI
├── static/
│   ├── css/style.css
│   └── js/script.js
├── tests/
│   ├── conftest.py               # Shared fixtures (DB, fastapi_server, Playwright)
│   ├── e2e/
│   │   └── test_fastapi_calculator.py   # Playwright E2E tests (positive + negative)
│   ├── integration/
│   │   ├── test_api.py
│   │   ├── test_calculation.py
│   │   ├── test_calculation_schema.py
│   │   ├── test_database.py
│   │   ├── test_dependencies.py
│   │   ├── test_get_db.py
│   │   ├── test_jwt.py
│   │   ├── test_schema_base.py
│   │   ├── test_user.py
│   │   └── test_user_auth.py
│   └── unit/
│       └── test_calculator.py
├── .github/
│   └── workflows/
│       └── ci.yml                # Linear pipeline: test → security → deploy
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── init-db.sh
├── pytest.ini
└── requirements.txt
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/KKS071/assignment13_jwt_auth_e2e.git
cd assignment13_jwt_auth_e2e
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your database URL and secret keys if needed
```

---

## JWT Authentication

### Registration — `POST /auth/register`

Accepts user data, validates it with Pydantic, hashes the password using bcrypt, and stores the new user. Returns a `UserResponse` on success or `400` if the username/email already exists.

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Doe",
    "username": "janedoe",
    "email": "jane@example.com",
    "password": "SecurePass1!",
    "confirm_password": "SecurePass1!"
  }'
```

### Login — `POST /auth/login`

Verifies the username/email and hashed password, then returns a JWT access token and refresh token.

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "janedoe", "password": "SecurePass1!"}'
```

### Pydantic Validation Rules

| Field | Rule |
|-------|------|
| `email` | Must be a valid email format |
| `password` | Min 8 chars, must include uppercase, lowercase, digit, and special character |
| `confirm_password` | Must match `password` |
| `username` | Min 3 characters |

### Using a Protected Endpoint

```bash
# Store the token from login, then pass it as a Bearer header
curl -H "Authorization: Bearer <access_token>" \
  http://127.0.0.1:8000/calculations
```

---

## Running the Backend

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs: http://127.0.0.1:8000/docs

### All API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | No | Create a new user |
| POST | `/auth/login` | No | Login and receive JWT tokens |
| POST | `/auth/token` | No | OAuth2 form login (Swagger UI) |
| GET | `/calculations` | Yes | List user's calculations |
| POST | `/calculations` | Yes | Run a new calculation |
| GET | `/calculations/{id}` | Yes | Get one calculation |
| PUT | `/calculations/{id}` | Yes | Update a calculation |
| DELETE | `/calculations/{id}` | Yes | Delete a calculation |
| GET | `/health` | No | Health check |

---

## Running the Frontend

The frontend is served directly by FastAPI using Jinja2 templates. Start the backend first, then visit:

| Page | URL |
|------|-----|
| Home | http://127.0.0.1:8000/ |
| Register | http://127.0.0.1:8000/register |
| Login | http://127.0.0.1:8000/login |
| Dashboard | http://127.0.0.1:8000/dashboard |

### Frontend Features

- **Registration page:** Client-side validation for email format, password strength (min 8 chars, uppercase, lowercase, digit), and password confirmation match. Shows a green success alert on success and redirects to login.
- **Login page:** Validates inputs client-side, posts credentials to `/auth/login`, stores the returned JWT in `localStorage`, then redirects to the dashboard.
- **Dashboard:** Reads the JWT from `localStorage` and includes it as a `Bearer` token on every calculation API request. Redirects to `/login` automatically if no token is present.

---

## Running pytest (All Tests)

All unit, integration, and E2E tests run in a single pytest command. Install Playwright browsers once before running:

```bash
# One-time browser install
playwright install --with-deps chromium

# Run all tests with coverage
pytest tests/ -v
```

View the HTML coverage report:

```bash
open htmlcov/index.html       # macOS
xdg-open htmlcov/index.html   # Linux
```

### Running specific suites

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# E2E tests only
pytest tests/e2e/ -m e2e -v --no-cov
```

---

## Running Playwright E2E Tests

The `fastapi_server` session fixture in `conftest.py` automatically starts the FastAPI server before E2E tests run — no manual server startup is needed.

```bash
playwright install --with-deps chromium
pytest tests/e2e/ -m e2e -v --no-cov
```

### E2E Test Coverage

| Test | Type | What it checks |
|------|------|----------------|
| `test_register_valid_user` | ✅ Positive | Valid registration shows success alert |
| `test_login_valid_user` | ✅ Positive | Correct credentials redirect to `/dashboard` |
| `test_register_short_password` | ❌ Negative | Short password shows error alert |
| `test_register_invalid_email` | ❌ Negative | Bad email format shows error alert |
| `test_login_wrong_password` | ❌ Negative | Wrong password shows error alert |

---

## Running with Docker

### Start the full stack

```bash
docker compose up --build
```

| Service | URL | Credentials |
|---------|-----|-------------|
| FastAPI app | http://localhost:8000 | — |
| pgAdmin | http://localhost:5050 | admin@example.com / admin |
| PostgreSQL | localhost:5432 | postgres / postgres |

### Connecting pgAdmin to the Database

pgAdmin does **not** auto-connect to PostgreSQL. On first login at http://localhost:5050:

1. Right-click **Servers** → **Register → Server…**
2. **General tab → Name:** `assignment13`
3. **Connection tab:**
   - Host: `db` ← Docker service name, **not** `localhost`
   - Port: `5432`
   - Database: `fastapi_db`
   - Username: `postgres`
   - Password: `postgres`
4. Click **Save**

You will now see `fastapi_db → Schemas → public → Tables` with `users` and `calculations`.

### Pull and run from Docker Hub

```bash
docker pull kks59/601_module13:latest
docker run -p 8000:8000 --env-file .env kks59/601_module13:latest
```

Docker Hub repo: https://hub.docker.com/r/kks59/601_module13

---

## CI/CD Pipeline

The pipeline runs on every push and pull request to `main` in a strict linear chain:

```
test  →  security  →  deploy
```

### Job 1 — `test`
- Spins up a PostgreSQL service container
- Installs all Python dependencies and Playwright + Chromium
- Runs **all tests** (unit + integration + E2E) in one `pytest tests/` call
- Uploads HTML coverage report and JUnit XML as artifacts

### Job 2 — `security` (runs after `test`)
- Builds the Docker image
- Scans with [Trivy](https://github.com/aquasecurity/trivy-action) for CRITICAL and HIGH CVEs
- Fails the pipeline if any unfixed vulnerabilities are found

### Job 3 — `deploy` (runs after `security`, on `main` branch only)
- Logs in to Docker Hub using GitHub Secrets
- Builds a multi-platform image (`linux/amd64`, `linux/arm64`)
- Pushes to `kks59/601_module13:latest` and `kks59/601_module13:<git-sha>`

### Required GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Value |
|--------|-------|
| `DOCKERHUB_USERNAME` | `kks59` |
| `DOCKERHUB_TOKEN` | Your Docker Hub access token |
