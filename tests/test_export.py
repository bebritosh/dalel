"""DOCX export: placeholders filled, guard runs on the final DOCX text."""

from __future__ import annotations

from datetime import date

import pytest

from app.models import Case
from app.services import export as export_mod
from app.services.claim import ClaimBuild
from app.services.claim_guard import GuardError
from app.services.export import ExportError, _docx_text, export_docx
from tests.test_pipeline import _confirm, _upload
from tests.conftest import create_case


def _legit_build() -> ClaimBuild:
    return ClaimBuild(
        text=(
            "Стоимость товара составила 249 990,00 KZT. "
            "Дата покупки: 05.11.2026."
        ),
        context={
            "seller": "ТОО «Пример Электроникс»",
            "item_desc": "Смартфон X",
            "purchase_date": "05.11.2026",
            "amount": "249 990,00",
            "currency": "KZT",
            "contact_date": "",
            "refusal_date": "",
            "legal": [{"title": "Право на товар надлежащего качества"}],
        },
        fact_ids=[],
        allowed_numbers={"249990.00"},
        allowed_dates={date(2026, 11, 5)},
    )


def test_export_has_no_unfilled_placeholders(monkeypatch):
    monkeypatch.setattr(export_mod, "build_claim", lambda s, c: _legit_build())
    _, data = export_docx(None, Case(id=1, access_token="x"))
    text = _docx_text(data)
    for marker in ("{{", "}}", "{%", "%}"):
        assert marker not in text
    assert "249 990,00" in text
    assert "Смартфон X" in text


def test_guard_blocks_substituted_amount_in_final_docx(monkeypatch):
    build = _legit_build()
    build.context["amount"] = "999 999,00"  # tampered: not in allowed_numbers
    monkeypatch.setattr(export_mod, "build_claim", lambda s, c: build)
    with pytest.raises(GuardError):
        export_docx(None, Case(id=1, access_token="x"))


def test_leftover_marker_in_data_raises_export_error(monkeypatch):
    build = _legit_build()
    build.context["seller"] = "{{ evil }}"  # markers must never survive render
    monkeypatch.setattr(export_mod, "build_claim", lambda s, c: build)
    with pytest.raises(ExportError):
        export_docx(None, Case(id=1, access_token="x"))


def test_real_pipeline_docx_has_values_and_no_markers(client):
    """Full path: the exported DOCX carries real values and no raw placeholders."""
    from pathlib import Path

    demo = Path("eval/cases/demo-001")
    case_id, token = create_case(client)
    h = {"X-Case-Token": token}
    _upload(client, case_id, token, "receipt.png", "receipt", "image/png")
    _upload(client, case_id, token, "chat.txt", "chat", "text/plain")
    facts = {f["field"]: f for f in client.post(f"/cases/{case_id}/extract", headers=h).json()}
    for field in ("seller_name", "purchase_date", "total_amount"):
        _confirm(client, token, facts[field]["id"])
    client.post(f"/cases/{case_id}/claim", headers=h)

    export = client.get(f"/cases/{case_id}/export?format=docx", headers=h)
    assert export.status_code == 200
    text = _docx_text(export.content)
    for marker in ("{{", "}}", "{%", "%}"):
        assert marker not in text
    assert "ПРЕТЕНЗИЯ" in text
    assert "249 990,00" in text
    _ = demo  # path kept for clarity
