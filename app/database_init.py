# File: app/database_init.py
# Purpose: Create and drop all DB tables

from app.database import engine
from app.models.user import Base  # noqa: F401 – registers all models


def init_db():
    Base.metadata.create_all(bind=engine)


def drop_db():
    Base.metadata.drop_all(bind=engine)


if __name__ == "__main__":
    init_db()  # pragma: no cover
