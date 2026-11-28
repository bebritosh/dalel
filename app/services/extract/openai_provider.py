"""OpenAI extraction provider: Chat Completions via httpx (no SDK).

The model receives numbered OCR lines and must return strict JSON (Structured
Outputs, ``response_format.type = json_schema`` with ``strict: true``) holding
only values and line_ids. Text and bboxes are copied by code elsewhere.

PRIVACY: this module never logs or includes in exceptions the OCR text, the
request body or the response body. Errors carry only status codes / generic
messages.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.models import OcrLine
from app.services.extract.base import LlmProvider
from app.services.extract.schema import ExtractionResult

_API_URL = "https://api.openai.com/v1/chat/completions"
_TIMEOUT = 60.0
_MAX_COMPLETION_TOKENS = 4000  # includes reasoning tokens on reasoning models

_SYSTEM = (
    "You extract fields from a retail receipt. You are given numbered OCR lines "
    "('<line_id>: <text>'). Return ONLY the JSON requested by the schema. "
    "Rules: every value MUST be copied from the referenced line_ids; never "
    "invent or compute values; use line ids exactly as given; purchase_date as "
    "YYYY-MM-DD; total_amount as a plain decimal string like 249990.00; "
    "currency as ISO code (KZT for ₸/тг/тенге); use null for a field that is "
    "absent or unreadable and list its name in 'unreadable'. confidence is 0..1."
)


class MissingOpenAiKeyError(RuntimeError):
    """Raised when OpenAI mode is selected but no API key is configured."""


class OpenAiError(RuntimeError):
    """Provider failure. The message never contains receipt content."""


def _field_schema() -> dict[str, Any]:
    return {
        "type": ["object", "null"],
        "properties": {
            "value": {"type": "string"},
            "line_ids": {"type": "array", "items": {"type": "integer"}},
            "confidence": {"type": "number"},
        },
        "required": ["value", "line_ids", "confidence"],
        "additionalProperties": False,
    }


# Strict mode: every property is required, additionalProperties is false and
# optional values are expressed as a type union with null.
STRICT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "document_type": {"type": "string"},
        "fields": {
            "type": "object",
            "properties": {
                "seller_name": _field_schema(),
                "purchase_date": _field_schema(),
                "total_amount": _field_schema(),
                "currency": _field_schema(),
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "qty": {"type": ["number", "null"]},
                            "price": {"type": ["string", "null"]},
                            "line_ids": {"type": "array", "items": {"type": "integer"}},
                        },
                        "required": ["name", "qty", "price", "line_ids"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": [
                "seller_name",
                "purchase_date",
                "total_amount",
                "currency",
                "items",
            ],
            "additionalProperties": False,
        },
        "unreadable": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["document_type", "fields", "unreadable"],
    "additionalProperties": False,
}


class OpenAiProvider(LlmProvider):
    """OpenAI-backed extraction provider (Structured Outputs)."""

    source = "openai"

    def __init__(
        self,
        api_key: str = "",
        model: str = "",
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self._transport = transport

    def _payload(self, lines: list[OcrLine]) -> dict[str, Any]:
        numbered = "\n".join(f"{l.line_no}: {l.text}" for l in lines)
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": f"OCR lines:\n{numbered}"},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "receipt_extraction",
                    "strict": True,
                    "schema": STRICT_SCHEMA,
                },
            },
            "max_completion_tokens": _MAX_COMPLETION_TOKENS,
        }

    def _call(self, payload: dict[str, Any]) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            with httpx.Client(timeout=_TIMEOUT, transport=self._transport) as client:
                resp = client.post(_API_URL, json=payload, headers=headers)
        except httpx.HTTPError as exc:
            # Only the exception class name: its text could echo request details.
            raise OpenAiError(f"OpenAI request failed ({type(exc).__name__})") from None
        if resp.status_code != 200:
            raise OpenAiError(f"OpenAI returned HTTP {resp.status_code}")
        try:
            choice = resp.json()["choices"][0]
        except (ValueError, KeyError, IndexError, TypeError):
            raise OpenAiError("OpenAI response has an unexpected shape") from None
        message = choice.get("message") or {}
        if message.get("refusal"):
            raise OpenAiError("OpenAI model refused the request")
        if choice.get("finish_reason") == "length":
            raise _BadOutput("response truncated (finish_reason=length)")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise _BadOutput("empty response content")
        return content

    def extract(self, sha256: str, lines: list[OcrLine]) -> ExtractionResult:
        if not self.api_key:
            raise MissingOpenAiKeyError(
                "LLM_MODE=openai requires OPENAI_API_KEY in .env. "
                "Set it, or use LLM_MODE=rules / fixture."
            )
        payload = self._payload(lines)
        last: str = ""
        for _attempt in range(2):  # one retry on schema/JSON problems
            try:
                content = self._call(payload)
                return ExtractionResult.model_validate(json.loads(content))
            except _BadOutput as exc:
                last = str(exc)
            except (json.JSONDecodeError, ValidationError):
                last = "response is not valid JSON for the schema"
        raise OpenAiError(f"OpenAI output rejected after retry: {last}")


class _BadOutput(Exception):
    """Internal: model output unusable; eligible for one retry."""
