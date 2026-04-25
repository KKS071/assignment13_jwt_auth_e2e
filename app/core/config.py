# File: app/core/config.py
# Purpose: App settings loaded from environment or .env file

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/fastapi_db"
    JWT_SECRET_KEY: str = "super-secret-key-change-in-production-min32chars"
    JWT_REFRESH_SECRET_KEY: str = "super-refresh-key-change-in-production-min32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 4  # low rounds = fast tests
    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


@lru_cache()
def get_settings() -> Settings:
    return Settings()
