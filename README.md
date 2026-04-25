# File: README.md
# Purpose: Project documentation, setup, and usage guide

# Assignment 13 – JWT Auth E2E

A FastAPI application with JWT authentication, PostgreSQL, Playwright E2E tests, and a full CI/CD pipeline.

- **GitHub:** https://github.com/KKS071/assignment13_jwt_auth_e2e
- **Docker Hub:** https://hub.docker.com/r/kks59/601_module13

---

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy, psycopg2, python-jose, passlib/bcrypt
- **Frontend:** Jinja2 templates, vanilla JS
- **Tests:** pytest, pytest-cov, Playwright
- **CI/CD:** GitHub Actions
- **Containers:** Docker, Docker Compose

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/KKS071/assignment13_jwt_auth_e2e.git
cd assignment13_jwt_auth_e2e
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your database URL and secret keys
```

---

## Running the Backend

Make sure PostgreSQL is running and the database exists, then:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API docs are available at: http://127.0.0.1:8000/docs

### Key endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create a new user |
| POST | `/auth/login` | Login and get JWT tokens |
| POST | `/auth/token` | OAuth2 form login (Swagger UI) |
| GET | `/calculations` | List user calculations (auth required) |
| POST | `/calculations` | Run a new calculation (auth required) |
| GET | `/health` | Health check |

---

## Running the Frontend

The frontend is served by FastAPI as HTML templates:

- **Home:** http://127.0.0.1:8000/
- **Register:** http://127.0.0.1:8000/register
- **Login:** http://127.0.0.1:8000/login
- **Dashboard:** http://127.0.0.1:8000/dashboard

---

## Running pytest

Requires a running PostgreSQL instance (see `.env`):

```bash
# All tests with coverage
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# With verbose output
pytest -v

# View HTML coverage report
open htmlcov/index.html
```

Coverage is enforced via `pytest.ini`. The target is 100% for `app/`.

---

## Running Playwright E2E Tests

Requires the FastAPI server to be running locally:

```bash
# Install Playwright browsers (first time only)
playwright install --with-deps chromium

# Start the server in one terminal
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Run E2E tests in another terminal
pytest tests/e2e/ -m e2e -v
```

### E2E test coverage

| Test | Type | Description |
|------|------|-------------|
| `test_register_valid_user` | ✅ Positive | Valid registration shows success alert |
| `test_login_valid_user` | ✅ Positive | Correct credentials redirect to dashboard |
| `test_register_short_password` | ❌ Negative | Short password shows error alert |
| `test_register_invalid_email` | ❌ Negative | Bad email format shows error alert |
| `test_login_wrong_password` | ❌ Negative | Wrong password shows error alert |

---

## Running with Docker

### Build and start everything

```bash
docker compose up --build
```

Services:
- FastAPI app → http://localhost:8000
- pgAdmin → http://localhost:5050 (admin@example.com / admin)

### Run just the app image

```bash
docker build -t jwt-auth-app .
docker run -p 8000:8000 --env-file .env jwt-auth-app
```

### Pull from Docker Hub

```bash
docker pull kks59/601_module13:latest
docker run -p 8000:8000 kks59/601_module13:latest
```

---

## CI/CD Pipeline

The pipeline runs on every push and pull request to `main`. It has four jobs:

### Job 1 – `test` (pytest)
- Spins up a PostgreSQL service container
- Installs dependencies
- Runs `pytest tests/unit/ tests/integration/` with `pytest-cov`
- Uploads HTML coverage report as an artifact

### Job 2 – `e2e` (Playwright) — runs after `test`
- Same PostgreSQL service
- Installs Playwright + Chromium
- Starts the FastAPI server automatically via `conftest.py` fixture
- Runs `pytest tests/e2e/ -m e2e`

### Job 3 – `security` (Trivy) — runs after `test`
- Builds the Docker image
- Scans with [Trivy](https://github.com/aquasecurity/trivy-action) for CRITICAL and HIGH CVEs
- Fails the build if unfixed critical/high vulnerabilities are found

### Job 4 – `deploy` — runs after `e2e` + `security`, on `main` branch only
- Logs in to Docker Hub using `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets
- Builds a multi-platform image (`linux/amd64`, `linux/arm64`)
- Pushes `kks59/601_module13:latest` and `kks59/601_module13:<git-sha>`

### Required GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Value |
|--------|-------|
| `DOCKERHUB_USERNAME` | `kks59` |
| `DOCKERHUB_TOKEN` | Your Docker Hub access token |

---

## Project Structure

```
assignment13_jwt_auth_e2e/
├── app/
│   ├── auth/
│   │   ├── dependencies.py   # FastAPI auth deps
│   │   └── jwt.py            # Token creation/verification
│   ├── core/
│   │   └── config.py         # Settings (pydantic-settings)
│   ├── models/
│   │   ├── calculation.py    # Calculation ORM model
│   │   └── user.py           # User ORM model with auth
│   ├── schemas/
│   │   ├── base.py           # Shared base schemas
│   │   ├── calculation.py    # Calculation schemas
│   │   ├── token.py          # Token schemas
│   │   └── user.py           # User schemas
│   ├── database.py           # Engine + session
│   ├── database_init.py      # Create/drop tables
│   ├── main.py               # FastAPI app + routes
│   └── operations.py         # Arithmetic helpers
├── templates/
│   ├── layout.html
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   └── dashboard.html
├── static/
│   ├── css/style.css
│   └── js/script.js
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   └── test_calculator.py
│   ├── integration/
│   │   ├── test_database.py
│   │   ├── test_dependencies.py
│   │   ├── test_schema_base.py
│   │   └── test_user_auth.py
│   └── e2e/
│       └── test_e2e.py
├── .github/
│   └── workflows/
│       └── ci.yml
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── init-db.sh
├── pytest.ini
└── requirements.txt
```
