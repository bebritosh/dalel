"""Claim export to DOCX.

Renders the docxtpl template with the grounded context when available; falls
back to building a plain DOCX from the authoritative claim text otherwise.
Re-runs the output guard as a final safety net before returning bytes.

PDF export is intentionally not implemented in this version (no LibreOffice
dependency). See HANDOFF.md for the rationale.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from docx import Document as DocxDocument
from docxtpl import DocxTemplate
from sqlmodel import Session

from app.models import Case
from app.services.claim import build_claim
from app.services.claim_guard import GuardError, check_text

_TEMPLATE = Path("templates/claim.docx")


def export_docx(session: Session, case: Case) -> tuple[str, bytes]:
    """Return (filename, docx_bytes) for a case's claim."""
    build = build_claim(session, case)

    violations = check_text(build.text, build.allowed_numbers, build.allowed_dates)
    if violations:
        raise GuardError(violations)

    buffer = BytesIO()
    if _TEMPLATE.exists():
        tpl = DocxTemplate(str(_TEMPLATE))
        tpl.render(build.context)
        tpl.save(buffer)
    else:
        doc = DocxDocument()
        for line in build.text.split("\n"):
            doc.add_paragraph(line)
        doc.save(buffer)

    filename = f"pretenziya_case_{case.id}.docx"
    return filename, buffer.getvalue()
