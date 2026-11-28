"""OCR engine selection and the run_ocr orchestration."""

from __future__ import annotations

from pathlib import Path

from sqlmodel import Session, select

from app.core.config import settings
from app.models import Document, DocumentKind, OcrLine
from app.services.ocr.base import OcrEngine
from app.services.ocr.fixture_engine import FIXTURES_DIR, FixtureOcrEngine

# Kinds that are OCR'd for field extraction.
OCR_KINDS = {DocumentKind.receipt, DocumentKind.warranty}


def ocr_mode() -> str:
    """Effective OCR mode. LLM_MODE=auto drives OCR auto-routing too."""
    return "auto" if settings.llm_mode == "auto" else settings.ocr_engine


def has_layout_fixture(sha256: str) -> bool:
    """True if a committed layout fixture exists for this file hash."""
    return (FIXTURES_DIR / f"{sha256}.layout.json").exists()


def get_ocr_engine(sha256: str | None = None) -> OcrEngine:
    """Return the OCR engine. Auto mode: known sha256 -> fixture, else Tesseract."""
    mode = ocr_mode()
    if mode == "auto":
        mode = "fixture" if sha256 and has_layout_fixture(sha256) else "tesseract"
    if mode == "tesseract":
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

    engine = get_ocr_engine(document.sha256)
    document.ocr_source = (
        "fixture" if isinstance(engine, FixtureOcrEngine) else "tesseract"
    )
    session.add(document)
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
