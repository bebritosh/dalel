"""OCR engine selection and the run_ocr orchestration."""

from __future__ import annotations

from pathlib import Path

from sqlmodel import Session, select

from app.core.config import settings
from app.models import Document, DocumentKind, OcrLine
from app.services.ocr.base import OcrEngine
from app.services.ocr.fixture_engine import FixtureOcrEngine

# Kinds that are OCR'd for field extraction.
OCR_KINDS = {DocumentKind.receipt, DocumentKind.warranty}


def get_ocr_engine() -> OcrEngine:
    """Return the configured OCR engine. Defaults to the fixture engine."""
    if settings.ocr_engine == "tesseract":
        # Imported lazily so pytesseract/Tesseract are only needed in this mode.
        from app.services.ocr.tesseract_engine import TesseractEngine

        return TesseractEngine(
            langs=settings.ocr_langs, tesseract_cmd=settings.tesseract_cmd
        )
    return FixtureOcrEngine()


def run_ocr(session: Session, document: Document) -> list[OcrLine]:
    """Recognize a document and persist its OCR lines (idempotent per document)."""
    existing = session.exec(
        select(OcrLine).where(OcrLine.document_id == document.id)
    ).all()
    if existing:
        return list(existing)

    if document.kind not in OCR_KINDS:
        return []

    engine = get_ocr_engine()
    data_lines = engine.recognize(Path(document.stored_path), document.mime_type)

    lines: list[OcrLine] = []
    for d in data_lines:
        line = OcrLine(
            document_id=document.id,
            line_no=d.line_no,
            text=d.text,
            bbox_x=d.bbox_x,
            bbox_y=d.bbox_y,
            bbox_w=d.bbox_w,
            bbox_h=d.bbox_h,
            page=d.page,
        )
        session.add(line)
        lines.append(line)
    session.commit()
    for line in lines:
        session.refresh(line)
    return lines
