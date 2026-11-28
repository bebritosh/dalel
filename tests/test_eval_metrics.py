"""Tests for the pure metric functions of eval/run_eval.py (no Tesseract)."""

from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "run_eval", Path(__file__).resolve().parent.parent / "eval" / "run_eval.py"
)
ev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ev)


def test_match_total_ignores_formatting():
    assert ev.match_total("389 900,00", "389900.00")
    assert not ev.match_total("389 000,00", "389900.00")
    assert not ev.match_total(None, "389900.00")


def test_match_date_and_currency():
    assert ev.match_date("14.03.2026", "2026-03-14")
    assert not ev.match_date("15.03.2026", "2026-03-14")
    assert ev.match_currency("kzt", "KZT")
    assert not ev.match_currency("КИТ", "KZT")


def test_match_seller_normalizes_quotes_and_case():
    assert ev.match_seller("ТОО Алем Техно", "ТОО «Алем Техно»")
    assert not ev.match_seller("TOO «Алем Техно»", "ТОО «Алем Техно»")  # Latin T


def test_match_items_share_of_gold_found():
    assert ev.match_items(["Пылесос Vortex 2000"], ["Пылесос Vortex 2000", "Фильтр HEPA"]) == 0.5
    assert ev.match_items([], ["x"]) == 0.0
    assert ev.match_items([], []) == 1.0


def test_value_in_text_and_recall():
    text = "Дата: 14.03.2026\nИТОГО: 389 900,00 KZT"
    assert ev.value_in_text("date", "2026-03-14", text)
    assert ev.value_in_text("number", "389900.00", text)
    assert not ev.value_in_text("number", "389901.00", text)
    gold = {"seller": "ТОО «Алем»", "purchase_date": "2026-03-14", "total_amount": "389900.00",
            "currency": "KZT", "items": []}
    r = ev.ocr_recall(gold, text)
    assert r["date"] and r["total"] and r["currency"] and not r["seller"]


def test_guard_blocks_substituted_amount():
    res = ev.guard_blocks_substitution(
        "Стоимость 389900.00 KZT. Дата: 14.03.2026.", "389900.00", {"389900.00"}, {date(2026, 3, 14)}
    )
    assert res == {"clean_passes": True, "substituted_blocked": True}


def test_safe_div():
    assert ev.safe_div(1, 0) is None
    assert ev.safe_div(1, 4) == 0.25
