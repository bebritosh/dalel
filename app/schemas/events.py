"""Schemas for timeline events."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.models.enums import EventKind


class EventRead(BaseModel):
    """A timeline event as shown to the user."""

    id: int
    date: date | None
    kind: EventKind
    description: str
    document_id: int | None
    message_id: str | None = None
    needs_review: bool
