"""Claim endpoints: create, export DOCX, mark sent."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session

from app.core.db import get_session
from app.core.security import get_authorized_case
from app.models import Case
from app.schemas.claim import ClaimRead, GuardErrorBody, GuardViolationOut, MarkSentOut
from app.services import cases as cases_service
from app.services.claim import RequiredFieldsError, create_claim
from app.services.claim_guard import GuardError
from app.services.export import (
    ExportError,
    SofficeUnavailableError,
    export_docx,
    export_pdf,
)

router = APIRouter(prefix="/cases", tags=["claim"])

_DOCX_MIME = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


def _guard_body(error: GuardError) -> dict:
    return GuardErrorBody(
        violations=[
            GuardViolationOut(value=v.value, kind=v.kind, hint=v.hint)
            for v in error.violations
        ]
    ).model_dump()


@router.post("/{case_id}/claim", response_model=ClaimRead)
def post_claim(
    case: Case = Depends(get_authorized_case),
    session: Session = Depends(get_session),
) -> ClaimRead:
    """Assemble and store the claim. 409 if fields unconfirmed, 422 if guard blocks."""
    try:
        claim = create_claim(session, case)
    except RequiredFieldsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "detail": "Не все обязательные поля подтверждены.",
                "missing": e.missing,
            },
        )
    except GuardError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=_guard_body(e)
        )
    return ClaimRead.model_validate(claim, from_attributes=True)


@router.get("/{case_id}/export")
def export(
    format: str = "docx",
    case: Case = Depends(get_authorized_case),
    session: Session = Depends(get_session),
) -> Response:
    """Export the claim as DOCX, or PDF when LibreOffice is available."""
    if format not in ("docx", "pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поддерживаются форматы docx и pdf.",
        )
    try:
        if format == "pdf":
            filename, data = export_pdf(session, case)
            media_type = "application/pdf"
        else:
            filename, data = export_docx(session, case)
            media_type = _DOCX_MIME
    except RequiredFieldsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "detail": "Не все обязательные поля подтверждены.",
                "missing": e.missing,
            },
        )
    except GuardError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=_guard_body(e)
        )
    except SofficeUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
    except ExportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка формирования DOCX: {e}",
        )
    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{case_id}/mark-sent", response_model=MarkSentOut)
def mark_sent(
    case: Case = Depends(get_authorized_case),
    session: Session = Depends(get_session),
) -> MarkSentOut:
    """Mark the claim as sent and start the 10-day response deadline."""
    updated = cases_service.mark_sent(session, case)
    return MarkSentOut(
        id=updated.id,
        status=updated.status,
        response_deadline=updated.response_deadline,
    )
