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
