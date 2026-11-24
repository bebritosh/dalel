"""Database engine and session management."""

from __future__ import annotations

from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

# check_same_thread=False is required for SQLite with FastAPI's threadpool.
_connect_args = {"check_same_thread": False}
engine = create_engine(settings.database_url, connect_args=_connect_args)


def create_db_and_tables() -> None:
    """Create all tables. Import models so they register with SQLModel.metadata."""
    import app.models  # noqa: F401  (ensures table classes are imported)

    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency that yields a database session."""
    with Session(engine) as session:
        yield session
