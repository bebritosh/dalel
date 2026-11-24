"""Read endpoints: timeline, missing evidence, validation checks."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.db import get_session
from app.core.security import get_authorized_case
from app.models import Case
from app.schemas.checks import CheckResult
from app.schemas.events import EventRead
from app.schemas.missing import MissingItemRead
from app.services.missing import get_missing
from app.services.timeline import build_events, get_timeline
from app.services.validate import run_checks

router = APIRouter(prefix="/cases", tags=["analysis"])


@router.get("/{case_id}/timeline", response_model=list[EventRead])
def timeline(
    case: Case = Depends(get_authorized_case),
    session: Session = Depends(get_session),
) -> list[EventRead]:
    """Return the ordered timeline (building events if needed)."""
    build_events(session, case.id)
    events = get_timeline(session, case.id)
    return [EventRead.model_validate(e, from_attributes=True) for e in events]


@router.get("/{case_id}/missing", response_model=list[MissingItemRead])
def missing(
    case: Case = Depends(get_authorized_case),
    session: Session = Depends(get_session),
) -> list[MissingItemRead]:
    """Return the missing-evidence findings (M1-M5)."""
    return get_missing(session, case.id)


@router.get("/{case_id}/checks", response_model=list[CheckResult])
def checks(
    case: Case = Depends(get_authorized_case),
    session: Session = Depends(get_session),
) -> list[CheckResult]:
    """Return the validation findings (V1-V4)."""
    return run_checks(session, case.id)
