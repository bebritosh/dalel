"""Fact edit/confirm endpoint: PATCH /facts/{fact_id}."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlmodel import Session, select

from app.core.db import get_session
from app.models import Case, Fact, OcrLine
from app.schemas.facts import FactPatch, FactRead
from app.services.extract.grounding import is_grounded

router = APIRouter(tags=["facts"])


def _ground_field_name(field: str) -> str:
    if field.startswith("item_") and field.endswith("_price"):
        return "price"
    if field.startswith("item_"):
        return "item"
    return field


def _authorized_fact(
    fact_id: int,
    x_case_token: str | None,
    session: Session,
) -> Fact:
    not_found = HTTPException(status_code=404, detail="Fact not found")
    if not x_case_token:
        raise not_found
    fact = session.get(Fact, fact_id)
    if fact is None:
        raise not_found
    case = session.get(Case, fact.case_id)
    if case is None or case.access_token != x_case_token:
        raise not_found
    return fact


@router.patch("/facts/{fact_id}", response_model=FactRead)
def patch_fact(
    fact_id: int,
    body: FactPatch,
    x_case_token: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> FactRead:
    """Edit a fact's value and/or confirm it (token required)."""
    fact = _authorized_fact(fact_id, x_case_token, session)

    if body.value is not None:
        fact.value = body.value
        lines = session.exec(
            select(OcrLine).where(OcrLine.document_id == fact.document_id)
        ).all()
        lines_by_id = {line.line_no: line for line in lines}
        fact.grounded = is_grounded(
            _ground_field_name(fact.field), fact.value, fact.line_ids, lines_by_id
        )
        fact.needs_review = not fact.grounded

    if body.confirmed_by_user is not None:
        fact.confirmed_by_user = body.confirmed_by_user
        if body.confirmed_by_user:
            fact.needs_review = False

    session.add(fact)
    session.commit()
    session.refresh(fact)
    return FactRead.model_validate(fact, from_attributes=True)
