"""Test fixtures: isolated temp database and temp data directory.

Tests never touch the real data/ folder or dalel.db. The app is created without
running its lifespan (so the production engine and data dir are left alone), and
get_session is overridden to use a fresh per-test SQLite file.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401  (register tables)
from app.core import config
from app.core.db import get_session
from app.main import app


@pytest.fixture(autouse=True)
def _offline_settings(monkeypatch) -> None:
    """Keep the suite offline whatever the developer's .env holds.

    A real OPENAI_API_KEY / LLM_MODE=auto in .env must not turn tests into paid
    network calls; tests that need another mode set it explicitly.
    """
    monkeypatch.setattr(config.settings, "openai_api_key", "")
    monkeypatch.setattr(config.settings, "anthropic_api_key", "")
    monkeypatch.setattr(config.settings, "llm_mode", "fixture")


@pytest.fixture()
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    """A TestClient wired to a temp DB and temp data directory."""
    monkeypatch.setattr(config.settings, "data_dir", str(tmp_path / "data"))

    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    # No `with`: lifespan is intentionally skipped so the real engine/data dir
    # are not initialized.
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def create_case(client: TestClient) -> tuple[int, str]:
    """Helper: create a case and return (id, access_token)."""
    resp = client.post("/cases")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    return body["id"], body["access_token"]
