# File: app/main.py
# Purpose: FastAPI application entry point with all routes

from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.database import Base, get_db, engine
from app.models.calculation import Calculation
from app.models.user import User
from app.schemas.calculation import CalculationBase, CalculationResponse, CalculationUpdate
from app.schemas.token import TokenResponse
from app.schemas.user import UserCreate, UserResponse, UserLogin


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="JWT Auth API", version="1.0.0", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ── Web pages ──────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, tags=["web"])
def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse, tags=["web"])
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse, tags=["web"])
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse, tags=["web"])
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


# ── Health ─────────────────────────────────────────────────────────────────

@app.get("/health", tags=["health"])
def read_health():
    return {"status": "ok"}


# ── Auth ───────────────────────────────────────────────────────────────────

@app.post("/auth/register", response_model=UserResponse, status_code=201, tags=["auth"])
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    user_data = user_create.model_dump(exclude={"confirm_password"})
    try:
        user = User.register(db, user_data)
        db.commit()
        db.refresh(user)
        return user
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login", response_model=TokenResponse, tags=["auth"])
def login_json(user_login: UserLogin, db: Session = Depends(get_db)):
    auth = User.authenticate(db, user_login.username, user_login.password)
    if auth is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = auth["user"]
    db.commit()

    expires_at = auth.get("expires_at") or datetime.now(timezone.utc) + timedelta(minutes=30)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return TokenResponse(
        access_token=auth["access_token"],
        refresh_token=auth["refresh_token"],
        token_type="bearer",
        expires_at=expires_at,
        user_id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_verified=user.is_verified,
    )


@app.post("/auth/token", tags=["auth"])
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 form login for Swagger UI."""
    auth = User.authenticate(db, form_data.username, form_data.password)
    if auth is None:
        raise HTTPException(status_code=401, detail="Invalid username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    db.commit()
    return {"access_token": auth["access_token"], "token_type": "bearer"}


# ── Calculations ───────────────────────────────────────────────────────────

@app.post("/calculations", response_model=CalculationResponse, status_code=201, tags=["calculations"])
def create_calculation(
    data: CalculationBase,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        calc = Calculation.create(data.type, current_user.id, data.inputs)
        calc.result = calc.get_result()
        db.add(calc)
        db.commit()
        db.refresh(calc)
        return calc
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/calculations", response_model=List[CalculationResponse], tags=["calculations"])
def list_calculations(current_user=Depends(get_current_active_user), db: Session = Depends(get_db)):
    return db.query(Calculation).filter(Calculation.user_id == current_user.id).all()


@app.get("/calculations/{calc_id}", response_model=CalculationResponse, tags=["calculations"])
def get_calculation(calc_id: str, current_user=Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        uid = UUID(calc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calculation id format.")
    calc = db.query(Calculation).filter(Calculation.id == uid, Calculation.user_id == current_user.id).first()
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found.")
    return calc


@app.put("/calculations/{calc_id}", response_model=CalculationResponse, tags=["calculations"])
def update_calculation(
    calc_id: str,
    update: CalculationUpdate,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        uid = UUID(calc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calculation id format.")
    calc = db.query(Calculation).filter(Calculation.id == uid, Calculation.user_id == current_user.id).first()
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found.")
    if update.inputs is not None:
        calc.inputs = update.inputs
        calc.result = calc.get_result()
    calc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(calc)
    return calc


@app.delete("/calculations/{calc_id}", status_code=204, tags=["calculations"])
def delete_calculation(calc_id: str, current_user=Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        uid = UUID(calc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calculation id format.")
    calc = db.query(Calculation).filter(Calculation.id == uid, Calculation.user_id == current_user.id).first()
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found.")
    db.delete(calc)
    db.commit()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="info")
