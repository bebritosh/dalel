"""Rule-based baseline extractor (regex over OCR lines). NOT an LLM.

Same interface as the LLM providers: returns values plus line_ids only. Text and
bounding boxes are copied later by code. Always call this "rule-based baseline".
"""

from __future__ import annotations

import re

from app.models import OcrLine
from app.services.extract.base import LlmProvider
from app.services.extract.normalize import iter_dates, iter_numbers, normalize_number
from app.services.extract.schema import (
    ExtractedField,
    ExtractedItem,
    ExtractionFields,
    ExtractionResult,
)

_TOTAL_RE = re.compile(r"\b(итого|итог|всего|к\s+оплате|total|sum)\b", re.IGNORECASE)
_STRONG_TOTAL_RE = re.compile(r"\b(итого|total)\b", re.IGNORECASE)
_CURRENCY_RE = re.compile(r"(₸|\bKZT\b|\bтг\b|\bтенге\b)", re.IGNORECASE)
_SEPARATOR_RE = re.compile(r"^[\s\-=_*.~#]{3,}$")
_QTY_PRICE_RE = re.compile(
    r"^\s*(\d+(?:[.,]\d+)?)\s*(?:шт\.?|pcs\.?|уп\.?)?\s*[xх×*]\s*(\d[\d\s.,]*)\s*$",
    re.IGNORECASE,
)
_SKIP_RE = re.compile(
    r"(кассир|чек\s*№|оплата|спасибо|дата|бин|иин|рнн|тел\.?|ккм|фп|card|карта|thank)",
    re.IGNORECASE,
)


def _is_separator(text: str) -> bool:
    return bool(_SEPARATOR_RE.match(text))


def _letters(text: str) -> int:
    return sum(ch.isalpha() for ch in text)


class RuleBasedProvider(LlmProvider):
    """Regex heuristics over OCR lines (rule-based baseline, not an LLM)."""

    source = "rules"

    def extract(self, sha256: str, lines: list[OcrLine]) -> ExtractionResult:
        ordered = sorted(lines, key=lambda l: l.line_no)
        unreadable: list[str] = []
        fields = ExtractionFields()

        seller = next(
            (
                l
                for l in ordered
                if _letters(l.text) >= 3 and not _is_separator(l.text)
            ),
            None,
        )
        if seller:
            fields.seller_name = ExtractedField(
                value=seller.text.strip(), line_ids=[seller.line_no], confidence=0.5
            )
        else:
            unreadable.append("seller_name")

        for l in ordered:
            dates = iter_dates(l.text)
            if dates:
                fields.purchase_date = ExtractedField(
                    value=dates[0].isoformat(), line_ids=[l.line_no], confidence=0.6
                )
                break
        if fields.purchase_date is None:
            unreadable.append("purchase_date")

        total_line = self._find_total_line(ordered)
        if total_line is not None:
            nums = iter_numbers(total_line.text)
            fields.total_amount = ExtractedField(
                value=nums[-1], line_ids=[total_line.line_no], confidence=0.6
            )
        else:
            unreadable.append("total_amount")

        cur_line = (
            total_line
            if total_line is not None and _CURRENCY_RE.search(total_line.text)
            else next((l for l in ordered if _CURRENCY_RE.search(l.text)), None)
        )
        if cur_line is not None:
            fields.currency = ExtractedField(
                value="KZT", line_ids=[cur_line.line_no], confidence=0.5
            )
        else:
            unreadable.append("currency")

        fields.items = self._find_items(ordered, total_line)
        return ExtractionResult(fields=fields, unreadable=unreadable)

    @staticmethod
    def _find_total_line(ordered: list[OcrLine]) -> OcrLine | None:
        with_num = [l for l in ordered if iter_numbers(l.text)]
        strong = [l for l in with_num if _STRONG_TOTAL_RE.search(l.text)]
        if strong:
            return strong[-1]
        weak = [l for l in with_num if _TOTAL_RE.search(l.text)]
        return weak[-1] if weak else None

    @staticmethod
    def _find_items(
        ordered: list[OcrLine], total_line: OcrLine | None
    ) -> list[ExtractedItem]:
        limit = total_line.line_no if total_line is not None else None
        items: list[ExtractedItem] = []
        prev: OcrLine | None = None
        for l in ordered:
            if limit is not None and l.line_no >= limit:
                break
            if _is_separator(l.text):
                prev = None
                continue
            m = _QTY_PRICE_RE.match(l.text)
            if m and prev is not None:
                price = normalize_number(m.group(2))
                if price:
                    items.append(
                        ExtractedItem(
                            name=prev.text.strip(),
                            qty=float(m.group(1).replace(",", ".")),
                            price=price,
                            line_ids=[prev.line_no, l.line_no],
                        )
                    )
                prev = None
                continue
            if _letters(l.text) >= 3 and not _SKIP_RE.search(l.text) and l.line_no > 0:
                # Header lines (seller, address) precede the first separator and
                # are only kept as candidates until a qty x price line follows.
                prev = l
            else:
                prev = None
        return items
