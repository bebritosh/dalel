"""Extraction endpoint: run OCR + LLM extraction and build timeline events."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.db import get_session
from app.core.security import get_authorized_case
from app.models import Case
from app.schemas.facts import FactRead
from app.services.extract import run_extraction
from app.services.timeline import build_events

router = APIRouter(prefix="/cases", tags=["extract"])


@router.post("/{case_id}/extract", response_model=list[FactRead])
def extract(
    case: Case = Depends(get_authorized_case),
    session: Session = Depends(get_session),
) -> list[FactRead]:
    """Extract receipt fields (grounded facts) and build timeline events."""
    facts = run_extraction(session, case)
    build_events(session, case.id)
    return [FactRead.model_validate(f, from_attributes=True) for f in facts]
