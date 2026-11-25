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

# Unrendered template tokens that must never survive into the final DOCX.
_PLACEHOLDER_MARKERS = ("{{", "}}", "{%", "%}")


class ExportError(Exception):
    """The rendered DOCX is malformed (e.g. an unfilled template placeholder)."""


def _docx_text(data: bytes) -> str:
    """Extract the visible paragraph text from DOCX bytes."""
    doc = DocxDocument(BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs)


def export_docx(session: Session, case: Case) -> tuple[str, bytes]:
    """Return (filename, docx_bytes) for a case's claim.

    Guards both the authoritative claim text and the final rendered DOCX text,
    and rejects any DOCX that still contains unfilled template placeholders.
    """
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
    data = buffer.getvalue()

    final_text = _docx_text(data)

    leftover = [m for m in _PLACEHOLDER_MARKERS if m in final_text]
    if leftover:
        raise ExportError(f"unfilled template placeholders in DOCX: {leftover}")

    # Re-run the guard against the FINAL DOCX text, not only the source text,
    # so a template/context mismatch cannot smuggle in an unbacked number/date.
    violations = check_text(final_text, build.allowed_numbers, build.allowed_dates)
    if violations:
        raise GuardError(violations)

    filename = f"pretenziya_case_{case.id}.docx"
    return filename, data
