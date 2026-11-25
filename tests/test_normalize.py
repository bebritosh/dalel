"""Tests for number/date normalization and grounding helpers."""

from __future__ import annotations

from datetime import date

from app.services.extract.normalize import (
    iter_dates,
    iter_numbers,
    normalize_date,
    normalize_number,
)


def test_normalize_number_spaces_and_comma():
    assert normalize_number("249 990,00") == "249990.00"
    assert normalize_number("249990.00") == "249990.00"
    assert normalize_number("1 000") == "1000.00"


def test_normalize_number_invalid():
    assert normalize_number("abc") is None


def test_iter_numbers_from_text():
    assert "249990.00" in iter_numbers("ИТОГО: 249 990,00 KZT")


def test_normalize_date_formats():
    assert normalize_date("2026-11-05") == date(2026, 11, 5)
    assert normalize_date("05.11.2026") == date(2026, 11, 5)
    assert normalize_date("Дата: 05.11.2026 14:32") == date(2026, 11, 5)


def test_iter_dates():
    assert date(2026, 11, 5) in iter_dates("куплено 05.11.2026 в магазине")


def test_item_price_and_total_are_stored_normalized():
    """Raw provider formatting ("27 990,00") is stored as "27990.00"."""
    from app.models import OcrLine
    from app.services.extract.schema import ExtractionResult
    from app.services.extract.service import _facts_from_result

    lines = {
        0: OcrLine(id=0, document_id=1, line_no=0, text="Наушники Pulse BT 1 шт x 27 990,00", bbox=[0, 0, 1, 1]),
        1: OcrLine(id=1, document_id=1, line_no=1, text="ИТОГО: 27 990,00 KZT", bbox=[0, 0, 1, 1]),
    }
    result = ExtractionResult.model_validate({
        "document_type": "receipt",
        "fields": {
            "total_amount": {"value": "27 990,00", "line_ids": [1], "confidence": 0.9},
            "items": [{"name": "Наушники Pulse BT", "qty": 1, "price": "27 990,00", "line_ids": [0]}],
        },
        "unreadable": [],
    })
    facts = {f.field: f for f in _facts_from_result(1, 1, result, lines)}
    assert facts["total_amount"].value == "27990.00"
    assert facts["total_amount"].grounded is True
    assert facts["item_1_price"].value == "27990.00"
    assert facts["item_1_price"].grounded is True
