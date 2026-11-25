"""The startup migration adds new columns to an old DB without losing data."""

from __future__ import annotations

from sqlalchemy import create_engine, inspect, text

from app.core import db


def _old_schema_engine(tmp_path):
    """An engine whose 'document' and 'event' tables predate the new columns."""
    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE document (id INTEGER PRIMARY KEY, case_id INTEGER NOT NULL, "
            "kind VARCHAR NOT NULL, stored_path VARCHAR NOT NULL, sha256 VARCHAR NOT NULL, "
            "mime_type VARCHAR NOT NULL, created_at DATETIME NOT NULL)"
        ))
        conn.execute(text(
            "INSERT INTO document (id, case_id, kind, stored_path, sha256, mime_type, created_at) "
            "VALUES (1, 1, 'receipt', 'x.png', 'abc', 'image/png', '2026-11-25T00:00:00')"
        ))
        conn.execute(text(
            "CREATE TABLE event (id INTEGER PRIMARY KEY, case_id INTEGER NOT NULL, "
            "date DATE, kind VARCHAR NOT NULL, description VARCHAR NOT NULL, "
            "document_id INTEGER, needs_review BOOLEAN NOT NULL)"
        ))
    return engine


def test_reconcile_adds_missing_columns_and_keeps_data(tmp_path, monkeypatch):
    engine = _old_schema_engine(tmp_path)
    monkeypatch.setattr(db, "engine", engine)

    applied = db.reconcile_columns()

    assert "document.ocr_source" in applied
    assert "document.extract_source" in applied
    assert "event.message_id" in applied

    cols = {c["name"] for c in inspect(engine).get_columns("document")}
    assert {"ocr_source", "extract_source"} <= cols

    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT sha256, ocr_source, extract_source FROM document WHERE id = 1"
        )).one()
    assert row[0] == "abc"  # existing data preserved
    assert row[1] == ""  # new NOT NULL string column defaulted to ''
    assert row[2] == ""


def test_reconcile_is_idempotent(tmp_path, monkeypatch):
    engine = _old_schema_engine(tmp_path)
    monkeypatch.setattr(db, "engine", engine)

    db.reconcile_columns()
    assert db.reconcile_columns() == []  # nothing left to add on a second pass
