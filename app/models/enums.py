"""Enumerations shared across models and schemas."""

from __future__ import annotations

from enum import Enum


class CaseStatus(str, Enum):
    """Lifecycle of a dispute case."""

    draft = "draft"
    extracted = "extracted"
    confirmed = "confirmed"
    claim_ready = "claim_ready"


class ClaimType(str, Enum):
    """Supported claim scenarios. MVP covers defective goods only."""

    defective_goods = "defective_goods"


class DocumentKind(str, Enum):
    """Kind of an uploaded document."""

    receipt = "receipt"
    chat = "chat"
    photo = "photo"
    warranty = "warranty"


class EventKind(str, Enum):
    """Kind of a timeline event."""

    purchase = "purchase"
    defect = "defect"
    contact = "contact"
    reply = "reply"
    refusal = "refusal"
    other = "other"
