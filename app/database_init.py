# File: app/database_init.py
# Purpose: Create and drop all DB tables (both models must be imported first)

from sqlalchemy import text
from app.database import engine, Base

# Import every model so SQLAlchemy's metadata knows all tables before drop_all
from app.models.user import User  # noqa: F401
from app.models.calculation import Calculation  # noqa: F401


def init_db():
    """Create all tables in dependency order."""
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Drop all tables using CASCADE to handle FK constraints cleanly."""
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS calculations CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        conn.commit()


if __name__ == "__main__":
    init_db()  # pragma: no cover
