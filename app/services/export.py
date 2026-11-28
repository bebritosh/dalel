"""Claim export to DOCX.

Renders the docxtpl template with the grounded context when available; falls
back to building a plain DOCX from the authoritative claim text otherwise.
Re-runs the output guard as a final safety net before returning bytes.

PDF export is intentionally not implemented in this version (no LibreOffice
dependency). See HANDOFF.md for the rationale.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

from docx import Document as DocxDocument
from docxtpl import DocxTemplate
from sqlmodel import Session

from app.core.config import settings
from app.models import Case
from app.services.claim import build_claim
from app.services.claim_guard import GuardError, check_text

_TEMPLATE = Path("templates/claim.docx")

# Unrendered template tokens that must never survive into the final DOCX.
_PLACEHOLDER_MARKERS = ("{{", "}}", "{%", "%}")

# Standard LibreOffice install locations to probe when SOFFICE_PATH is unset.
_SOFFICE_CANDIDATES = (
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    "/usr/bin/soffice",
    "/opt/libreoffice/program/soffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
)


class ExportError(Exception):
    """The rendered DOCX is malformed (e.g. an unfilled template placeholder)."""


class SofficeUnavailableError(Exception):
    """LibreOffice (soffice) is not installed or the conversion failed."""


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


def find_soffice() -> str | None:
    """Locate the LibreOffice binary: SOFFICE_PATH, then PATH, then standards."""
    if settings.soffice_path and Path(settings.soffice_path).exists():
        return settings.soffice_path
    on_path = shutil.which("soffice") or shutil.which("soffice.exe")
    if on_path:
        return on_path
    for candidate in _SOFFICE_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


def export_pdf(session: Session, case: Case) -> tuple[str, bytes]:
    """Return (filename, pdf_bytes) by rendering the guarded DOCX via LibreOffice.

    Raises SofficeUnavailableError if LibreOffice is absent or conversion fails.
    """
    _, docx_bytes = export_docx(session, case)  # reuse guard + placeholder checks

    soffice = find_soffice()
    if not soffice:
        raise SofficeUnavailableError(
            "LibreOffice (soffice) не найден. Установите LibreOffice и задайте "
            "SOFFICE_PATH в .env, либо экспортируйте DOCX."
        )

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        docx_path = tmp_dir / f"claim_{case.id}.docx"
        docx_path.write_bytes(docx_bytes)
        try:
            subprocess.run(
                [soffice, "--headless", "--convert-to", "pdf", "--outdir",
                 str(tmp_dir), str(docx_path)],
                check=True, capture_output=True, timeout=120,
            )
        except (subprocess.SubprocessError, OSError) as exc:
            raise SofficeUnavailableError(
                f"Конвертация в PDF не удалась: {type(exc).__name__}."
            ) from exc
        pdf_path = docx_path.with_suffix(".pdf")
        if not pdf_path.exists():
            raise SofficeUnavailableError("LibreOffice не создал PDF-файл.")
        pdf_bytes = pdf_path.read_bytes()

    return f"pretenziya_case_{case.id}.pdf", pdf_bytes
