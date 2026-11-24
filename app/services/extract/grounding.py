"""Grounding: verify an extracted value actually occurs in its OCR lines.

This enforces the core invariant: a value is trusted only if code can find it
in the exact OCR lines the model pointed to (after normalizing numbers/dates).
"""

from __future__ import annotations

import re

from app.models import OcrLine
from app.services.extract.normalize import (
    iter_dates,
    iter_numbers,
    normalize_date,
    normalize_number,
)

DATE_FIELDS = {"purchase_date"}
NUMERIC_FIELDS = {"total_amount", "price"}


def _collect_text(line_ids: list[int], lines_by_id: dict[int, OcrLine]) -> str:
    return " ".join(
        lines_by_id[i].text for i in line_ids if i in lines_by_id
    )


def _norm_text(text: str) -> str:
    text = text.replace(" ", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", text).strip().casefold()


def is_grounded(
    field: str,
    value: str,
    line_ids: list[int],
    lines_by_id: dict[int, OcrLine],
) -> bool:
    """Return True if value is found in the referenced OCR lines."""
    if not value or not line_ids:
        return False
    text = _collect_text(line_ids, lines_by_id)
    if not text:
        return False

    if field in DATE_FIELDS:
        target = normalize_date(value)
        return target is not None and target in iter_dates(text)

    if field in NUMERIC_FIELDS:
        target = normalize_number(value)
        return target is not None and target in iter_numbers(text)

    # String fields (seller_name, currency, item name): normalized substring.
    return _norm_text(value) in _norm_text(text)
