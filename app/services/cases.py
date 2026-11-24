"""Case lifecycle service: create and delete."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlmodel import Session, delete, select

from app.core import storage
from app.models import (
    Case,
    CaseStatus,
    Claim,
    ClaimType,
    Document,
    Event,
    Fact,
    MissingItem,
    OcrLine,
)


def create_case(session: Session, claim_type: ClaimType) -> Case:
    """Create a draft case with a fresh access token."""
    case = Case(
        status=CaseStatus.draft,
        claim_type=claim_type,
        access_token=uuid.uuid4().hex,
    )
    session.add(case)
    session.commit()
    session.refresh(case)
    return case


def delete_case(session: Session, case: Case) -> None:
    """Delete a case, all its child records, and its files on disk."""
    case_id = case.id
    assert case_id is not None

    # Delete OCR lines belonging to this case's documents.
    doc_ids = session.exec(
        select(Document.id).where(Document.case_id == case_id)
    ).all()
    if doc_ids:
        session.exec(delete(OcrLine).where(OcrLine.document_id.in_(doc_ids)))

    for model in (Fact, Event, MissingItem, Claim, Document):
        session.exec(delete(model).where(model.case_id == case_id))

    session.delete(case)
    session.commit()

    storage.delete_case_files(case_id)


def mark_sent(session: Session, case: Case, days: int = 10) -> Case:
    """Mark the claim as sent and start the seller response deadline."""
    case.response_deadline = date.today() + timedelta(days=days)
    session.add(case)
    session.commit()
    session.refresh(case)
    return case
