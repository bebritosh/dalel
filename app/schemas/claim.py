"""Schemas for claims and guard violations."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import CaseStatus


class ClaimRead(BaseModel):
    """A generated claim."""

    id: int
    version: int
    text: str
    fact_ids: list[int]
    created_at: datetime


class GuardViolationOut(BaseModel):
    """One disallowed value reported to the client."""

    value: str
    kind: str
    hint: str


class GuardErrorBody(BaseModel):
    """422 body when the output guard blocks export."""

    detail: str = "Экспорт заблокирован: в тексте есть значения без подтверждённого факта."
    violations: list[GuardViolationOut] = Field(default_factory=list)


class MarkSentOut(BaseModel):
    """Response after marking a claim as sent."""

    id: int
    status: CaseStatus
    response_deadline: date | None
