"""Output guard: every number and date in the claim must be an allowed value.

Allowed values are the normalized numbers/dates of confirmed facts plus event
dates. Any extra number or date blocks export. This enforces the invariant that
the claim cannot contain an invented amount or date.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.services.extract.normalize import iter_dates, iter_numbers


@dataclass
class GuardViolation:
    """One disallowed value found in the claim text."""

    value: str
    kind: str  # "number" | "date"
    hint: str


class GuardError(Exception):
    """Raised when the claim contains values not backed by confirmed facts."""

    def __init__(self, violations: list[GuardViolation]) -> None:
        self.violations = violations
        super().__init__(f"{len(violations)} disallowed value(s) in claim")


def check_text(
    text: str,
    allowed_numbers: set[str],
    allowed_dates: set[date],
) -> list[GuardViolation]:
    """Return every number/date in text that is not in the allowed sets."""
    violations: list[GuardViolation] = []
    for num in iter_numbers(text):
        if num not in allowed_numbers:
            violations.append(
                GuardViolation(
                    value=num,
                    kind="number",
                    hint="Подтвердите поле с этим значением или уберите число из текста.",
                )
            )
    for d in iter_dates(text):
        if d not in allowed_dates:
            violations.append(
                GuardViolation(
                    value=d.isoformat(),
                    kind="date",
                    hint="Подтвердите дату события или уберите её из текста.",
                )
            )
    # De-duplicate by (value, kind), preserving order.
    seen: set[tuple[str, str]] = set()
    unique: list[GuardViolation] = []
    for v in violations:
        key = (v.value, v.kind)
        if key not in seen:
            seen.add(key)
            unique.append(v)
    return unique
