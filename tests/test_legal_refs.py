"""Legal references: real citations, copied verbatim, guard stays strict."""

from __future__ import annotations

import json
import zipfile
from io import BytesIO
from pathlib import Path
from xml.dom import minidom

from docx import Document as DocxDocument

from app.services.claim_guard import check_text, legal_citations
from tests.conftest import create_case
from tests.test_pipeline import _confirm, _upload

REFS = json.loads(Path("rules/legal_refs.json").read_text(encoding="utf-8"))


def test_every_ref_has_citation_source_and_check_date():
    for ref in REFS["refs"]:
        assert ref["citation"] and ref["text"], ref["id"]
        assert ref["source_url"].startswith("https://adilet.zan.kz/"), ref["id"]
        assert ref["checked_at"], ref["id"]
        # Honest status: nobody has signed these off yet.
        assert ref["lawyer_reviewed"] is False, ref["id"]


def test_exact_citation_is_exempt_but_other_numbers_still_block():
    cite = legal_citations()[0]
    assert check_text(f"Основание: {cite}.", set(), set()) == []
    # A citation not in the file (invented article) is blocked.
    assert check_text("Основание: ст. 99 Закона РК «О защите прав потребителей».", set(), set())
    # A substituted amount next to a real citation is still blocked.
    assert check_text(f"{cite}: вернуть 999 999,00 KZT.", {"249990.00"}, set())


def _demo_claim(client):
    case_id, token = create_case(client)
    h = {"X-Case-Token": token}
    _upload(client, case_id, token, "receipt.png", "receipt", "image/png")
    facts = client.post(f"/cases/{case_id}/extract", headers=h).json()
    for f in facts:
        if f["field"] in ("seller_name", "purchase_date", "total_amount", "currency"):
            assert _confirm(client, token, f["id"]).status_code == 200
    claim = client.post(f"/cases/{case_id}/claim", headers=h)
    assert claim.status_code == 200, claim.text
    return case_id, h, claim.json()["text"]


def test_claim_cites_every_ref_and_has_no_stub_marker(client):
    _, _, text = _demo_claim(client)
    assert "уточняется юристом" not in text
    for ref in REFS["refs"]:
        assert f"— {ref['citation']}: {ref['text']}." in text


def test_docx_mirrors_claim_text_and_is_valid_a4(client):
    case_id, h, text = _demo_claim(client)
    resp = client.get(f"/cases/{case_id}/export?format=docx", headers=h)
    assert resp.status_code == 200
    data = resp.content
    with zipfile.ZipFile(BytesIO(data)) as z:
        for name in z.namelist():
            if name.endswith(".xml") or name.endswith(".rels"):
                minidom.parseString(z.read(name))  # every XML part is well-formed
    doc = DocxDocument(BytesIO(data))
    docx_lines = [p.text for p in doc.paragraphs if p.text.strip()]
    text_lines = [ln for ln in text.split("\n") if ln.strip()]
    assert docx_lines == text_lines
    section = doc.sections[0]
    assert round(section.page_width.cm, 1) == 21.0
    assert round(section.page_height.cm, 1) == 29.7
