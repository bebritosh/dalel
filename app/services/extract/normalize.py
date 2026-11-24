"""Normalization helpers for numbers and dates.

Grounding compares an LLM-reported value against OCR line text after
normalizing both sides, so that "249 990,00" and "249990.00" match, and
"05.11.2026" matches the ISO date "2026-11-05".
"""

from __future__ import annotations

import re
from datetime import date

# A number token inside free text, allowing spaces/thin spaces as thousands
# separators and comma or dot as the decimal separator.
_NUMBER_RE = re.compile(r"\d[\d\s  .,]*\d|\d")

# Common date formats seen on receipts and in chats.
_DATE_PATTERNS = [
    (re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"), ("y", "m", "d")),
    (re.compile(r"\b(\d{1,2})[./](\d{1,2})[./](\d{4})\b"), ("d", "m", "y")),
    (re.compile(r"\b(\d{1,2})[./](\d{1,2})[./](\d{2})\b"), ("d", "m", "yy")),
]


def normalize_number(raw: str) -> str | None:
    """Return a canonical numeric string like '249990.00', or None.

    Removes thousands separators (spaces), converts a decimal comma to a dot.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    text = text.replace(" ", " ").replace(" ", " ")
    # Keep only digits, spaces, comma, dot.
    text = re.sub(r"[^\d\s.,]", "", text)
    text = text.strip()
    if not text:
        return None
    # Drop spaces (thousands separators).
    text = text.replace(" ", "")
    # If both comma and dot present, assume the last one is the decimal sep.
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    else:
        text = text.replace(",", ".")
    try:
        value = float(text)
    except ValueError:
        return None
    return f"{value:.2f}"


def iter_numbers(text: str) -> list[str]:
    """Return all canonical numbers found in free text."""
    results: list[str] = []
    for match in _NUMBER_RE.finditer(text or ""):
        norm = normalize_number(match.group(0))
        if norm is not None:
            results.append(norm)
    return results


def normalize_date(raw: str) -> date | None:
    """Parse the first date found in text into a date object, or None."""
    if raw is None:
        return None
    text = str(raw).strip()
    for pattern, order in _DATE_PATTERNS:
        m = pattern.search(text)
        if not m:
            continue
        parts = dict(zip(order, m.groups()))
        try:
            year = int(parts["y"]) if "y" in parts else 2000 + int(parts["yy"])
            return date(year, int(parts["m"]), int(parts["d"]))
        except (ValueError, KeyError):
            continue
    return None


def iter_dates(text: str) -> list[date]:
    """Return all dates found in free text."""
    results: list[date] = []
    for pattern, order in _DATE_PATTERNS:
        for m in pattern.finditer(text or ""):
            parts = dict(zip(order, m.groups()))
            try:
                year = int(parts["y"]) if "y" in parts else 2000 + int(parts["yy"])
                results.append(date(year, int(parts["m"]), int(parts["d"])))
            except (ValueError, KeyError):
                continue
    return results
