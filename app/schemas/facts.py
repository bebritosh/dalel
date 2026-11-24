"""Schemas for facts."""

from __future__ import annotations

from pydantic import BaseModel


class FactRead(BaseModel):
    """An extracted field as shown to the user."""

    id: int
    field: str
    value: str
    confidence: float
    document_id: int | None
    line_ids: list[int]
    grounded: bool
    needs_review: bool
    confirmed_by_user: bool


class FactPatch(BaseModel):
    """Manual edit and/or confirmation of a fact."""

    value: str | None = None
    confirmed_by_user: bool | None = None
