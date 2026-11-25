"""Tests for rule-based, OpenAI providers and auto-mode routing."""

from __future__ import annotations

import json
import logging

import httpx
import pytest

from app.core import config
from app.models import OcrLine
from app.services.extract import service
from app.services.extract.grounding import is_grounded
from app.services.extract.fixture_provider import FixtureProvider
from app.services.extract.openai_provider import (
    STRICT_SCHEMA,
    MissingOpenAiKeyError,
    OpenAiError,
    OpenAiProvider,
)
from app.services.extract.rules_provider import RuleBasedProvider
from app.services.ocr import factory
from app.services.ocr.fixture_engine import FixtureOcrEngine

DEMO_SHA = "eeef4d42540cb180e8328a558f69031d688e2664b14dc133479aa6a930fca1b3"
TEXTS = [
    "ТОО «Пример Электроникс»",
    "г. Алматы, пр. Абая 150",
    "Чек № 000123",
    "Дата: 05.11.2026 14:32",
    "Кассир: Иванова А.",
    "--------------------------------",
    "Смартфон X 128GB",
    "1 шт x 249 990,00",
    "--------------------------------",
    "ИТОГО: 249 990,00 KZT",
    "Оплата: карта",
]


def _lines(texts=TEXTS) -> list[OcrLine]:
    return [OcrLine(document_id=1, line_no=i, text=t) for i, t in enumerate(texts)]


# ---------- rule-based baseline ----------

def test_rules_extracts_demo_receipt():
    lines = _lines()
    res = RuleBasedProvider().extract("x", lines)
    f = res.fields
    by_id = {l.line_no: l for l in lines}
    assert f.seller_name.value == "ТОО «Пример Электроникс»"
    assert f.purchase_date.value == "2026-11-05"
    assert f.total_amount.value == "249990.00"
    assert f.currency.value == "KZT"
    assert f.items[0].name == "Смартфон X 128GB"
    assert f.items[0].price == "249990.00" and f.items[0].qty == 1
    for name in ("seller_name", "purchase_date", "total_amount", "currency"):
        fld = getattr(f, name)
        assert is_grounded(name, fld.value, fld.line_ids, by_id), name


def test_rules_missing_fields_reported_unreadable():
    res = RuleBasedProvider().extract("x", _lines(["-----", "12345"]))
    assert res.fields.total_amount is None
    assert {"seller_name", "purchase_date", "total_amount"} <= set(res.unreadable)


# ---------- OpenAI provider ----------

GOOD = {
    "document_type": "receipt",
    "fields": {
        "seller_name": {"value": "ТОО «Пример Электроникс»", "line_ids": [0], "confidence": 0.9},
        "purchase_date": {"value": "2026-11-05", "line_ids": [3], "confidence": 0.9},
        "total_amount": {"value": "249990.00", "line_ids": [9], "confidence": 0.9},
        "currency": None,
        "items": [{"name": "Смартфон X 128GB", "qty": None, "price": "249990.00", "line_ids": [6, 7]}],
    },
    "unreadable": ["currency"],
}


def _resp(content: str, finish="stop", status=200, refusal=None):
    body = {"choices": [{"finish_reason": finish, "message": {"content": content, "refusal": refusal}}]}
    return httpx.Response(status, json=body)


def _provider(handler) -> OpenAiProvider:
    return OpenAiProvider(api_key="sk-test-secret", model="m", transport=httpx.MockTransport(handler))


def test_openai_request_shape_and_result():
    seen = {}

    def handler(request: httpx.Request):
        seen["body"] = json.loads(request.content)
        seen["auth"] = request.headers["authorization"]
        return _resp(json.dumps(GOOD))

    res = _provider(handler).extract("sha", _lines())
    body = seen["body"]
    rf = body["response_format"]
    assert rf["type"] == "json_schema" and rf["json_schema"]["strict"] is True
    assert "max_completion_tokens" in body and "max_tokens" not in body
    assert "3: Дата: 05.11.2026 14:32" in body["messages"][1]["content"]
    assert res.fields.total_amount.line_ids == [9]
    assert res.fields.currency is None and res.fields.items[0].qty is None


def test_strict_schema_all_required_no_extra():
    def walk(node):
        if isinstance(node, dict):
            if node.get("properties"):
                assert node.get("additionalProperties") is False
                assert set(node["required"]) == set(node["properties"])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(STRICT_SCHEMA)


def test_openai_retries_once_on_bad_json():
    calls = []

    def handler(request):
        calls.append(1)
        return _resp("not json") if len(calls) == 1 else _resp(json.dumps(GOOD))

    assert _provider(handler).extract("s", _lines()).fields.seller_name is not None
    assert len(calls) == 2


def test_openai_fails_clearly_after_second_bad_output():
    calls = []

    def handler(request):
        calls.append(1)
        return _resp(json.dumps({"fields": {"seller_name": {"value": 5}}}))

    with pytest.raises(OpenAiError, match="after retry"):
        _provider(handler).extract("s", _lines())
    assert len(calls) == 2


def test_openai_http_error_and_missing_key(monkeypatch):
    p = _provider(lambda r: httpx.Response(401, json={"error": "x"}))
    with pytest.raises(OpenAiError, match="HTTP 401"):
        p.extract("s", _lines())
    monkeypatch.setattr(config.settings, "openai_api_key", "")
    with pytest.raises(MissingOpenAiKeyError):
        OpenAiProvider(api_key="", model="m").extract("s", _lines())


def test_openai_never_leaks_receipt_text_or_key(caplog):
    secret_text = "СЕКРЕТНЫЙ-ТЕКСТ-ЧЕКА"
    caplog.set_level(logging.DEBUG)
    p = _provider(lambda r: _resp("garbage " + secret_text))
    with pytest.raises(OpenAiError) as ei:
        p.extract("s", _lines([secret_text, "Дата: 05.11.2026"]))
    assert secret_text not in str(ei.value) and "sk-test-secret" not in str(ei.value)
    assert secret_text not in caplog.text and "sk-test-secret" not in caplog.text


# ---------- invariants: values only, code copies text, ungrounded -> review ----------

def test_ungrounded_value_needs_review():
    lines = _lines()
    bad = json.loads(json.dumps(GOOD))
    bad["fields"]["total_amount"]["value"] = "999999.00"  # not in line 9
    res = _provider(lambda r: _resp(json.dumps(bad))).extract("s", lines)
    facts = service._facts_from_result(1, 1, res, {l.line_no: l for l in lines})
    total = next(f for f in facts if f.field == "total_amount")
    assert total.needs_review and not total.grounded and total.confidence <= 0.3
    # Facts carry values + line_ids only; no text/bbox attributes copied from model.
    assert not hasattr(total, "text") and not hasattr(total, "bbox_x")


# ---------- auto-mode routing ----------

def test_auto_known_sha_uses_fixtures(monkeypatch):
    monkeypatch.setattr(config.settings, "llm_mode", "auto")
    monkeypatch.setattr(config.settings, "openai_api_key", "sk-x")
    assert isinstance(service.get_provider(DEMO_SHA), FixtureProvider)
    assert isinstance(factory.get_ocr_engine(DEMO_SHA), FixtureOcrEngine)


def test_auto_unknown_sha_routes_live(monkeypatch):
    monkeypatch.setattr(config.settings, "llm_mode", "auto")
    monkeypatch.setattr(config.settings, "openai_api_key", "sk-x")
    assert isinstance(service.get_provider("0" * 64), OpenAiProvider)
    monkeypatch.setattr(config.settings, "openai_api_key", "")
    assert isinstance(service.get_provider("0" * 64), RuleBasedProvider)
    # Unknown sha -> Tesseract engine (class resolved lazily; skip if module absent).
    try:
        from app.services.ocr.tesseract_engine import TesseractEngine
    except ImportError:
        pytest.skip("tesseract engine not available")
    assert isinstance(factory.get_ocr_engine("0" * 64), TesseractEngine)


def test_mode_routing(monkeypatch):
    for mode, cls in (("rules", RuleBasedProvider), ("openai", OpenAiProvider), ("fixture", FixtureProvider)):
        monkeypatch.setattr(config.settings, "llm_mode", mode)
        assert isinstance(service.get_provider(DEMO_SHA), cls)


def test_provenance_in_api(client, monkeypatch):
    from tests.conftest import create_case
    from tests.test_pipeline import _upload

    monkeypatch.setattr(config.settings, "llm_mode", "auto")
    case_id, token = create_case(client)
    h = {"X-Case-Token": token}
    _upload(client, case_id, token, "receipt.png", "receipt", "image/png")
    client.post(f"/cases/{case_id}/extract", headers=h)
    docs = client.get(f"/cases/{case_id}", headers=h).json()["documents"]
    rec = next(d for d in docs if d["kind"] == "receipt")
    assert rec["ocr_source"] == "fixture" and rec["extract_source"] == "fixture"
