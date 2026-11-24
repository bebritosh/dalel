"""Tests for the document upload endpoint."""

from __future__ import annotations

from app.core import config
from tests.conftest import create_case

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64  # minimal non-empty png-like bytes


def _upload(client, case_id, token, *, filename, kind, content, mime="application/octet-stream"):
    return client.post(
        f"/cases/{case_id}/documents",
        headers={"X-Case-Token": token},
        data={"kind": kind},
        files={"file": (filename, content, mime)},
    )


def test_upload_receipt_ok(client):
    case_id, token = create_case(client)
    resp = _upload(client, case_id, token, filename="r.png", kind="receipt", content=PNG)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["kind"] == "receipt"
    assert body["mime_type"] == "image/png"
    assert len(body["sha256"]) == 64
    # It shows up in the case view.
    case = client.get(f"/cases/{case_id}", headers={"X-Case-Token": token}).json()
    assert len(case["documents"]) == 1


def test_upload_txt_and_json_allowed(client):
    case_id, token = create_case(client)
    r1 = _upload(client, case_id, token, filename="chat.txt", kind="chat", content=b"hi")
    r2 = _upload(client, case_id, token, filename="chat.json", kind="chat", content=b"{}")
    assert r1.status_code == 201
    assert r2.status_code == 201


def test_upload_wrong_type_is_415(client):
    case_id, token = create_case(client)
    resp = _upload(client, case_id, token, filename="bad.gif", kind="photo", content=PNG)
    assert resp.status_code == 415


def test_upload_invalid_kind_is_422(client):
    case_id, token = create_case(client)
    resp = _upload(client, case_id, token, filename="r.png", kind="invoice", content=PNG)
    assert resp.status_code == 422


def test_upload_duplicate_is_409(client):
    case_id, token = create_case(client)
    r1 = _upload(client, case_id, token, filename="r.png", kind="receipt", content=PNG)
    assert r1.status_code == 201
    r2 = _upload(client, case_id, token, filename="r2.png", kind="receipt", content=PNG)
    assert r2.status_code == 409


def test_upload_too_large_is_413(client, monkeypatch):
    monkeypatch.setattr(config.settings, "max_upload_bytes", 10)
    case_id, token = create_case(client)
    resp = _upload(client, case_id, token, filename="r.png", kind="receipt", content=PNG)
    assert resp.status_code == 413


def test_upload_without_token_is_404(client):
    case_id, _ = create_case(client)
    resp = client.post(
        f"/cases/{case_id}/documents",
        data={"kind": "receipt"},
        files={"file": ("r.png", PNG, "image/png")},
    )
    assert resp.status_code == 404
