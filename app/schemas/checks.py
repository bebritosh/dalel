"""Schema for validation check results."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CheckResult(BaseModel):
    """One validation finding (V1-V4)."""

    code: str
    severity: str  # error | warning
    message: str
    fact_ids: list[int] = Field(default_factory=list)
    event_ids: list[int] = Field(default_factory=list)
    document_ids: list[int] = Field(default_factory=list)
