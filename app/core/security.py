"""Per-case access-token security.

Every path with a case id requires the X-Case-Token header. Any mismatch,
missing token, or unknown case returns 404 so that case existence is not
revealed to callers without the token.
"""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Path, status
from sqlmodel import Session

from app.core.db import get_session
from app.models import Case


def get_authorized_case(
    case_id: int = Path(..., ge=1),
    x_case_token: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> Case:
    """Load the case only if the supplied token matches. Otherwise 404."""
    not_found = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Case not found"
    )
    if not x_case_token:
        raise not_found
    case = session.get(Case, case_id)
    if case is None or case.access_token != x_case_token:
        raise not_found
    return case
