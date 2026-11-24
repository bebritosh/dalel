"""Request/response schemas for cases."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import CaseStatus, ClaimType
from app.schemas.documents import DocumentRead
from app.schemas.facts import FactRead


class CaseCreate(BaseModel):
    """Payload to create a case. Only defective_goods is supported for MVP."""

    claim_type: ClaimType = ClaimType.defective_goods


class CaseCreated(BaseModel):
    """Response to case creation: the id and the secret access token."""

    id: int
    access_token: str


class CaseRead(BaseModel):
    """Full case view: the case, its documents and extracted facts."""

    id: int
    status: CaseStatus
    claim_type: ClaimType
    created_at: datetime
    response_deadline: date | None
    documents: list[DocumentRead]
    facts: list[FactRead]
    receipt_document_id: int | None = None
