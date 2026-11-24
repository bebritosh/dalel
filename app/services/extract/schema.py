"""Pydantic schema for the strict JSON an LLM provider must return.

The LLM returns only values and OCR line numbers (line_ids). Line text and
bounding boxes are copied by code from OcrLine, never by the model.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractedField(BaseModel):
    """A single scalar field with its grounding line ids."""

    value: str
    line_ids: list[int] = Field(default_factory=list)
    confidence: float = 0.0


class ExtractedItem(BaseModel):
    """A line item on the receipt."""

    name: str
    qty: float | None = None
    price: str | None = None
    line_ids: list[int] = Field(default_factory=list)


class ExtractionFields(BaseModel):
    """The set of fields we try to extract from a receipt."""

    seller_name: ExtractedField | None = None
    purchase_date: ExtractedField | None = None
    total_amount: ExtractedField | None = None
    currency: ExtractedField | None = None
    items: list[ExtractedItem] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    """Full strict response from a provider."""

    document_type: str = "receipt"
    fields: ExtractionFields = Field(default_factory=ExtractionFields)
    unreadable: list[str] = Field(default_factory=list)
