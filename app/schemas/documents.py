"""Request/response schemas for documents."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import DocumentKind


class DocumentRead(BaseModel):
    """A stored document as returned to clients. No disk path is exposed."""

    id: int
    case_id: int
    kind: DocumentKind
    sha256: str
    mime_type: str
    created_at: datetime


class OcrLineRead(BaseModel):
    """One OCR line with its bounding box (image pixel coordinates)."""

    id: int
    line_no: int
    text: str
    bbox_x: int
    bbox_y: int
    bbox_w: int
    bbox_h: int
    page: int
