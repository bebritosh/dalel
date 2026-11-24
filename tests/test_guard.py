"""Tests for the output guard, including a deliberately injected fake amount."""

from __future__ import annotations

from datetime import date

from app.services.claim_guard import GuardError, check_text


def test_guard_passes_for_allowed_values():
    text = "Сумма 249 990,00 от 05.11.2026."
    violations = check_text(
        text,
        allowed_numbers={"249990.00"},
        allowed_dates={date(2026, 11, 5)},
    )
    assert violations == []


def test_guard_blocks_invented_amount():
    # A fabricated amount that is not among the allowed (confirmed) values.
    text = "Прошу вернуть 999 999,00 тенге."
    violations = check_text(text, allowed_numbers={"249990.00"}, allowed_dates=set())
    assert any(v.value == "999999.00" and v.kind == "number" for v in violations)


def test_guard_blocks_invented_date():
    text = "Дата покупки 01.01.2000."
    violations = check_text(text, allowed_numbers=set(), allowed_dates=set())
    assert any(v.kind == "date" for v in violations)


def test_guard_error_carries_violations():
    violations = check_text("100,00", {"200.00"}, set())
    err = GuardError(violations)
    assert err.violations == violations
