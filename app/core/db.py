"""Database engine, session management, and lightweight SQLite migration.

The migration is non-destructive: on startup it only ADDs columns that exist in
the models but not yet in the on-disk SQLite tables. It never drops or rewrites
data, so upgrading no longer requires deleting data/dalel.db. For a full reset
use scripts/reset_db.py.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# check_same_thread=False is required for SQLite with FastAPI's threadpool.
_connect_args = {"check_same_thread": False}
engine = create_engine(settings.database_url, connect_args=_connect_args)


def _default_literal(column) -> str | None:
    """SQLite literal for a column's python-side default, or None if unknown."""
    default = column.default
    if default is not None and not default.is_callable:
        value = default.arg
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            return "'" + value.replace("'", "''") + "'"
    type_name = str(column.type).upper()
    if any(t in type_name for t in ("CHAR", "TEXT", "CLOB")):
        return "''"
    if any(t in type_name for t in ("INT", "BOOL")):
        return "0"
    return None


def reconcile_columns() -> list[str]:
    """ADD COLUMN for model columns missing from existing SQLite tables.

    Returns the list of "table.column" changes applied. Brand-new tables are
    handled by create_all and skipped here.
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    applied: list[str] = []

    for table in SQLModel.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue
        db_cols = {c["name"] for c in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in db_cols:
                continue
            col_type = column.type.compile(dialect=engine.dialect)
            ddl = f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {col_type}'
            if not column.nullable:
                literal = _default_literal(column)
                # SQLite rejects a NOT NULL add without a default on a non-empty
                # table; fall back to a nullable column rather than failing.
                if literal is not None:
                    ddl += f" NOT NULL DEFAULT {literal}"
            with engine.begin() as conn:
                conn.execute(text(ddl))
            applied.append(f"{table.name}.{column.name}")

    if applied:
        logger.info("db migration: added columns %s", applied)
    return applied


def create_db_and_tables() -> None:
    """Create missing tables, then add any missing columns to existing ones."""
    import app.models  # noqa: F401  (ensures table classes are imported)

    SQLModel.metadata.create_all(engine)
    reconcile_columns()


def get_session() -> Iterator[Session]:
    """FastAPI dependency that yields a database session."""
    with Session(engine) as session:
        yield session
