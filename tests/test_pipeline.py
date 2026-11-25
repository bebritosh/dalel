"""End-to-end backend test over the synthetic demo case (fixture mode)."""

from __future__ import annotations

from pathlib import Path

from tests.conftest import create_case

DEMO = Path("eval/cases/demo-001")


def _upload(client, case_id, token, filename, kind, mime):
    content = (DEMO / filename).read_bytes()
    return client.post(
        f"/cases/{case_id}/documents",
        headers={"X-Case-Token": token},
        data={"kind": kind},
        files={"file": (filename, content, mime)},
    )


def _confirm(client, token, fact_id, value=None):
    body = {"confirmed_by_user": True}
    if value is not None:
        body["value"] = value
    return client.patch(
        f"/facts/{fact_id}", headers={"X-Case-Token": token}, json=body
    )


def test_full_pipeline(client):
    case_id, token = create_case(client)
    h = {"X-Case-Token": token}

    assert _upload(client, case_id, token, "receipt.png", "receipt", "image/png").status_code == 201
    assert _upload(client, case_id, token, "chat.txt", "chat", "text/plain").status_code == 201

    # Extraction produces grounded facts.
    facts = client.post(f"/cases/{case_id}/extract", headers=h).json()
    by_field = {f["field"]: f for f in facts}
    for field in ("seller_name", "purchase_date", "total_amount", "currency"):
        assert by_field[field]["grounded"] is True, field

    # Timeline has purchase, contact and refusal.
    timeline = client.get(f"/cases/{case_id}/timeline", headers=h).json()
    kinds = {e["kind"] for e in timeline}
    assert {"purchase", "contact", "refusal"} <= kinds

    # Missing: warranty and defect media are open; contact/refusal resolved.
    missing = {m["rule_id"]: m for m in client.get(f"/cases/{case_id}/missing", headers=h).json()}
    assert missing["M1"]["resolved"] is False
    assert missing["M3"]["resolved"] is False
    assert missing["M2"]["resolved"] is True
    assert missing["M4"]["resolved"] is True

    # Checks: no error-severity findings on the clean demo.
    checks = client.get(f"/cases/{case_id}/checks", headers=h).json()
    assert all(c["severity"] != "error" for c in checks), checks

    # Claim blocked until required fields are confirmed.
    assert client.post(f"/cases/{case_id}/claim", headers=h).status_code == 409

    for field in ("seller_name", "purchase_date", "total_amount"):
        assert _confirm(client, token, by_field[field]["id"]).status_code == 200

    # Claim now builds and passes the guard.
    claim = client.post(f"/cases/{case_id}/claim", headers=h)
    assert claim.status_code == 200, claim.text
    assert "ПРЕТЕНЗИЯ" in claim.json()["text"]

    # DOCX export works and looks like a zip (docx).
    export = client.get(f"/cases/{case_id}/export?format=docx", headers=h)
    assert export.status_code == 200
    assert export.content[:2] == b"PK"

    # Mark sent sets a response deadline.
    sent = client.post(f"/cases/{case_id}/mark-sent", headers=h).json()
    assert sent["response_deadline"] is not None


def test_unknown_export_format_is_400(client):
    case_id, token = create_case(client)
    resp = client.get(
        f"/cases/{case_id}/export?format=rtf", headers={"X-Case-Token": token}
    )
    assert resp.status_code == 400
