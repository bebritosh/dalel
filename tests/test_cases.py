"""Tests for case endpoints."""

from __future__ import annotations

from tests.conftest import create_case


def test_create_case_returns_id_and_token(client):
    resp = client.post("/cases")
    assert resp.status_code == 201
    body = resp.json()
    assert isinstance(body["id"], int)
    assert body["access_token"]


def test_create_case_default_claim_type(client):
    case_id, token = create_case(client)
    resp = client.get(f"/cases/{case_id}", headers={"X-Case-Token": token})
    assert resp.status_code == 200
    assert resp.json()["claim_type"] == "defective_goods"
    assert resp.json()["status"] == "draft"


def test_get_case_without_token_is_404(client):
    case_id, _ = create_case(client)
    assert client.get(f"/cases/{case_id}").status_code == 404


def test_get_case_with_wrong_token_is_404(client):
    case_id, _ = create_case(client)
    resp = client.get(f"/cases/{case_id}", headers={"X-Case-Token": "wrong"})
    assert resp.status_code == 404


def test_get_unknown_case_is_404(client):
    resp = client.get("/cases/9999", headers={"X-Case-Token": "whatever"})
    assert resp.status_code == 404


def test_delete_case_removes_it(client):
    case_id, token = create_case(client)
    resp = client.delete(f"/cases/{case_id}", headers={"X-Case-Token": token})
    assert resp.status_code == 204
    # Gone afterwards.
    resp = client.get(f"/cases/{case_id}", headers={"X-Case-Token": token})
    assert resp.status_code == 404


def test_delete_case_without_token_is_404(client):
    case_id, _ = create_case(client)
    assert client.delete(f"/cases/{case_id}").status_code == 404


def test_delete_case_removes_files_and_records(client, tmp_path):
    from pathlib import Path

    case_id, token = create_case(client)
    h = {"X-Case-Token": token}
    png = b"\x89PNG\r\n\x1a\n" + b"1" * 64
    up = client.post(
        f"/cases/{case_id}/documents",
        headers=h,
        data={"kind": "receipt"},
        files={"file": ("r.png", png, "image/png")},
    )
    assert up.status_code == 201
    files_dir = Path(tmp_path / "data" / "cases" / str(case_id))
    assert any(files_dir.iterdir())

    assert client.delete(f"/cases/{case_id}", headers=h).status_code == 204
    assert not files_dir.exists() or not any(files_dir.iterdir())
    assert client.get(f"/cases/{case_id}/documents/{up.json()['id']}/file", headers=h).status_code == 404


def test_delete_case_with_wrong_token_keeps_case(client):
    case_id, token = create_case(client)
    assert client.delete(f"/cases/{case_id}", headers={"X-Case-Token": "bad"}).status_code == 404
    assert client.get(f"/cases/{case_id}", headers={"X-Case-Token": token}).status_code == 200


def test_mark_sent_stores_deadline(client):
    from datetime import date, timedelta

    case_id, token = create_case(client)
    h = {"X-Case-Token": token}
    assert client.get(f"/cases/{case_id}", headers=h).json()["response_deadline"] is None
    resp = client.post(f"/cases/{case_id}/mark-sent", headers=h)
    assert resp.status_code == 200, resp.text
    expected = (date.today() + timedelta(days=10)).isoformat()
    assert resp.json()["response_deadline"] == expected
    # Persisted and visible in the case view.
    assert client.get(f"/cases/{case_id}", headers=h).json()["response_deadline"] == expected


def test_photo_upload_resolves_missing_m3(client):
    case_id, token = create_case(client)
    h = {"X-Case-Token": token}

    def m3() -> bool:
        items = client.get(f"/cases/{case_id}/missing", headers=h).json()
        return next(i for i in items if i["rule_id"] == "M3")["resolved"]

    assert m3() is False
    png = b"\x89PNG\r\n\x1a\n" + b"2" * 64
    up = client.post(
        f"/cases/{case_id}/documents",
        headers=h,
        data={"kind": "photo"},
        files={"file": ("defect.png", png, "image/png")},
    )
    assert up.status_code == 201
    assert m3() is True
