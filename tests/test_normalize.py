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
