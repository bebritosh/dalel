"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import analysis, cases, claim, documents, extract, facts
from app.core.config import settings
from app.core.db import create_db_and_tables
from app.core.logging import setup_logging
from app.core.storage import data_root


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize logging, storage, and the database on startup."""
    setup_logging()
    data_root()
    create_db_and_tables()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(cases.router)
app.include_router(documents.router)
app.include_router(extract.router)
app.include_router(facts.router)
app.include_router(analysis.router)
app.include_router(claim.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok", "app": settings.app_name}
