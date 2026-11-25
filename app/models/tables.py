"""SQLModel table definitions for the DÄLEL domain.

JSON columns (line_ids, fact_ids) store lists of integers. Document content is
never stored in these tables beyond OCR line text extracted on purpose.
"""

from datetime import date as date_type
from datetime import datetime, timezone

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.models.enums import CaseStatus, ClaimType, DocumentKind, EventKind


def _utcnow() -> datetime:
    """Timezone-aware UTC now (this sqlmodel stores datetimes as UTC-aware)."""
    return datetime.now(timezone.utc)


class Case(SQLModel, table=True):
    """A single consumer dispute case."""

    id: int | None = Field(default=None, primary_key=True)
    status: CaseStatus = Field(default=CaseStatus.draft)
    claim_type: ClaimType = Field(default=ClaimType.defective_goods)
    access_token: str = Field(index=True)
    created_at: datetime = Field(default_factory=_utcnow)
    response_deadline: date_type | None = Field(default=None)


class Document(SQLModel, table=True):
    """An uploaded document belonging to a case."""

    id: int | None = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="case.id", index=True)
    kind: DocumentKind
    stored_path: str  # path on disk, uuid filename only
    sha256: str = Field(index=True)
    mime_type: str
    created_at: datetime = Field(default_factory=_utcnow)
    # Provenance: "fixture" | "tesseract" ; "fixture" | "openai" | "anthropic" | "rules".
    # Empty until OCR / extraction has run. Fresh DB needed when upgrading.
    ocr_source: str = ""
    extract_source: str = ""


class OcrLine(SQLModel, table=True):
    """A single OCR line with its bounding box (phase 1 populates these)."""

    id: int | None = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id", index=True)
    line_no: int
    text: str
    bbox_x: int = 0
    bbox_y: int = 0
    bbox_w: int = 0
    bbox_h: int = 0
    page: int = 0


class Fact(SQLModel, table=True):
    """An extracted field value, grounded in OCR lines and confirmed by the user."""

    id: int | None = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="case.id", index=True)
    field: str
    value: str
    confidence: float = 0.0
    document_id: int | None = Field(default=None, foreign_key="document.id")
    line_ids: list[int] = Field(default_factory=list, sa_column=Column(JSON))
    grounded: bool = False  # value was found in the referenced OCR lines
    needs_review: bool = True
    confirmed_by_user: bool = False


class Event(SQLModel, table=True):
    """A timeline event (purchase, defect, contact, refusal, other)."""

    id: int | None = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="case.id", index=True)
    date: date_type | None = Field(default=None)
    kind: EventKind
    description: str = ""
    document_id: int | None = Field(default=None, foreign_key="document.id")
    needs_review: bool = True


class MissingItem(SQLModel, table=True):
    """A missing-evidence finding produced by the rules engine."""

    id: int | None = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="case.id", index=True)
    rule_id: str
    title: str
    why: str = ""
    fix: str = ""
    resolved: bool = False


class Claim(SQLModel, table=True):
    """A generated claim document (text + referenced facts)."""

    id: int | None = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="case.id", index=True)
    version: int = 1
    text: str = ""
    fact_ids: list[int] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=_utcnow)
