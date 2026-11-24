"""Document upload endpoint."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.security import get_authorized_case
from app.models import Case, Document, DocumentKind, OcrLine
from app.schemas.documents import DocumentRead, OcrLineRead
from app.services.ingest import ingest_document
from app.services.ocr import run_ocr

router = APIRouter(prefix="/cases", tags=["documents"])


def _case_document(session: Session, case: Case, doc_id: int) -> Document:
    doc = session.get(Document, doc_id)
    if doc is None or doc.case_id != case.id:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post(
    "/{case_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    kind: DocumentKind = Form(...),
    file: UploadFile = File(...),
    case: Case = Depends(get_authorized_case),
    session: Session = Depends(get_session),
) -> DocumentRead:
    """Upload one document to a case (token required).

    An invalid kind yields 422 (handled by FastAPI). Bad type -> 415,
    too large -> 413, duplicate -> 409 (handled by the ingest service).
    """
    content = await file.read()
    document = ingest_document(
        session=session,
        case=case,
        kind=kind,
        filename=file.filename,
        content=content,
    )
    return DocumentRead.model_validate(document, from_attributes=True)


@router.get("/{case_id}/documents/{doc_id}/lines", response_model=list[OcrLineRead])
def document_lines(
    doc_id: int,
    case: Case = Depends(get_authorized_case),
    session: Session = Depends(get_session),
) -> list[OcrLineRead]:
    """Return a document's OCR lines (running OCR if not done yet)."""
    doc = _case_document(session, case, doc_id)
    lines = session.exec(select(OcrLine).where(OcrLine.document_id == doc.id)).all()
    if not lines:
        lines = run_ocr(session, doc)
    return [OcrLineRead.model_validate(line, from_attributes=True) for line in lines]


@router.get("/{case_id}/documents/{doc_id}/file")
def document_file(
    doc_id: int,
    case: Case = Depends(get_authorized_case),
    session: Session = Depends(get_session),
) -> Response:
    """Return the stored document bytes (e.g. the receipt image)."""
    doc = _case_document(session, case, doc_id)
    path = Path(doc.stored_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return Response(content=path.read_bytes(), media_type=doc.mime_type)
