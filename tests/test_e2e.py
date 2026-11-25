"""End-to-end pipeline for both chat sources, fully offline (no OPENAI_API_KEY).

Covers the API path: upload -> extract (fixture) -> timeline events from the
chat -> confirm -> claim -> DOCX. WhatsApp uses chat.txt, Telegram uses
chat.json. The UI path over the same backend is captured in frontend/screenshots
and documented in docs/E2E.md.
"""

from __future__ import annotations

from pathlib import Path

from app.core.config import settings
from tests.conftest import create_case
from tests.test_pipeline import _confirm, _upload

WA = Path("eval/cases/demo-001")
TG = Path("eval/cases/demo-tg-001")


def _run(client, chat_name, chat_mime, chat_dir):
    case_id, token = create_case(client)
    h = {"X-Case-Token": token}
    assert _upload(client, case_id, token, "receipt.png", "receipt", "image/png").status_code == 201
    # Upload the chat from the given case directory.
    content = (chat_dir / chat_name).read_bytes()
    up = client.post(
        f"/cases/{case_id}/documents",
        headers=h,
        data={"kind": "chat"},
        files={"file": (chat_name, content, chat_mime)},
    )
    assert up.status_code == 201, up.text

    facts = {f["field"]: f for f in client.post(f"/cases/{case_id}/extract", headers=h).json()}
    for field in ("seller_name", "purchase_date", "total_amount", "currency"):
        assert facts[field]["grounded"] is True, field

    timeline = client.get(f"/cases/{case_id}/timeline", headers=h).json()
    kinds = {e["kind"] for e in timeline}
    assert {"purchase", "contact", "refusal"} <= kinds

    for field in ("seller_name", "purchase_date", "total_amount"):
        assert _confirm(client, token, facts[field]["id"]).status_code == 200

    claim = client.post(f"/cases/{case_id}/claim", headers=h)
    assert claim.status_code == 200, claim.text
    export = client.get(f"/cases/{case_id}/export?format=docx", headers=h)
    assert export.status_code == 200 and export.content[:2] == b"PK"
    return timeline


def test_no_openai_key_in_test_env():
    """The whole suite runs offline; these E2E paths must need no API key."""
    assert settings.openai_api_key == ""


def test_e2e_whatsapp(client):
    timeline = _run(client, "chat.txt", "text/plain", WA)
    chat_events = [e for e in timeline if e["kind"] in ("contact", "reply", "refusal")]
    # WhatsApp events carry a "line:N" source id.
    assert all(e["message_id"].startswith("line:") for e in chat_events)


def test_e2e_telegram(client):
    timeline = _run(client, "chat.json", "application/json", TG)
    chat_events = [e for e in timeline if e["kind"] in ("contact", "reply", "refusal")]
    # Telegram events carry the numeric message id.
    assert chat_events and all(e["message_id"].isdigit() for e in chat_events)


def test_e2e_rules_mode_offline(client, monkeypatch):
    """Extraction in rules mode works over fixture OCR with no API key."""
    monkeypatch.setattr(settings, "llm_mode", "rules")
    case_id, token = create_case(client)
    h = {"X-Case-Token": token}
    _upload(client, case_id, token, "receipt.png", "receipt", "image/png")
    facts = client.post(f"/cases/{case_id}/extract", headers=h).json()
    assert any(f["field"] == "total_amount" and f["value"] for f in facts)
