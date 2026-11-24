"""Schema for missing-evidence items."""

from __future__ import annotations

from pydantic import BaseModel


class MissingItemRead(BaseModel):
    """A missing-evidence finding (M1-M5)."""

    rule_id: str
    title: str
    why: str
    fix: str
    resolved: bool
