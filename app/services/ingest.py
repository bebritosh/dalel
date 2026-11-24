"""Document ingestion: validate, deduplicate, store on disk, record in DB."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.core import storage
from app.core.config import settings
from app.core.logging import get_logger
from app.models import Case, Document, DocumentKind

logger = get_logger(__name__)


def ingest_document(
    session: Session,
    case: Case,
    kind: DocumentKind,
    filename: str | None,
    content: bytes,
) -> Document:
    """Validate and store an uploaded document.

    Raises HTTPException with 415 (bad type), 413 (too large), or 409 (duplicate).
    Never logs document content.
    """
    ext = storage.extension_for(filename)
    if ext is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type",
        )

    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="File too large",
        )

    digest = storage.sha256_hex(content)
    existing = session.exec(
        select(Document).where(
            Document.case_id == case.id, Document.sha256 == digest
        )
    ).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate document",
        )

    stored_path = storage.save_bytes(case.id, content, ext)
    document = Document(
        case_id=case.id,
        kind=kind,
        stored_path=str(stored_path),
        sha256=digest,
        mime_type=storage.ALLOWED_TYPES[ext],
    )
    session.add(document)
    session.commit()
    session.refresh(document)
    logger.info(
        "ingested document id=%s case=%s kind=%s bytes=%s",
        document.id,
        case.id,
        kind.value,
        len(content),
    )
    return document
