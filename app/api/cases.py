"""Case endpoints: create, read, delete."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.security import get_authorized_case
from app.models import Case, Document, DocumentKind, Fact
from app.schemas.cases import CaseCreate, CaseCreated, CaseRead
from app.schemas.documents import DocumentRead
from app.schemas.facts import FactRead
from app.services import cases as cases_service

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseCreated, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CaseCreate | None = None,
    session: Session = Depends(get_session),
) -> CaseCreated:
    """Create a new draft case and return its id and access token."""
    claim_type = (payload or CaseCreate()).claim_type
    case = cases_service.create_case(session, claim_type)
    return CaseCreated(id=case.id, access_token=case.access_token)


@router.get("/{case_id}", response_model=CaseRead)
def read_case(
    case: Case = Depends(get_authorized_case),
    session: Session = Depends(get_session),
) -> CaseRead:
    """Return the case with its documents (token required)."""
    documents = session.exec(
        select(Document).where(Document.case_id == case.id)
    ).all()
    facts = session.exec(select(Fact).where(Fact.case_id == case.id)).all()
    receipt = next((d for d in documents if d.kind == DocumentKind.receipt), None)
    return CaseRead(
        id=case.id,
        status=case.status,
        claim_type=case.claim_type,
        created_at=case.created_at,
        response_deadline=case.response_deadline,
        documents=[DocumentRead.model_validate(d, from_attributes=True) for d in documents],
        facts=[FactRead.model_validate(f, from_attributes=True) for f in facts],
        receipt_document_id=receipt.id if receipt else None,
    )


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(
    case: Case = Depends(get_authorized_case),
    session: Session = Depends(get_session),
) -> None:
    """Delete the case, its records, and its files (token required)."""
    cases_service.delete_case(session, case)
