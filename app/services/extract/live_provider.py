"""Live extraction provider: calls the Anthropic Messages API via httpx.

Uses httpx (already a dependency) rather than a new SDK. The model receives the
numbered OCR lines and must return strict JSON with values and line_ids only.
Requires ANTHROPIC_API_KEY; raises a clear error when it is missing.
"""

from __future__ import annotations

import json

import httpx

from app.core.config import settings
from app.models import OcrLine
from app.services.extract.base import LlmProvider
from app.services.extract.schema import ExtractionResult

_API_URL = "https://api.anthropic.com/v1/messages"
_SYSTEM = (
    "You extract fields from a receipt. You are given numbered OCR lines. "
    "Return ONLY strict JSON matching this shape: "
    '{"document_type":"receipt","fields":{"seller_name":{"value":str,'
    '"line_ids":[int],"confidence":float},"purchase_date":{"value":"YYYY-MM-DD",'
    '"line_ids":[int],"confidence":float},"total_amount":{"value":str,'
    '"line_ids":[int],"confidence":float},"currency":{"value":str,'
    '"line_ids":[int],"confidence":float},"items":[{"name":str,"qty":number,'
    '"price":str,"line_ids":[int]}]},"unreadable":[str]}. '
    "Every value MUST be copied verbatim from the referenced line_ids. "
    "Do not invent values. Use line numbers exactly as given."
)


class MissingApiKeyError(RuntimeError):
    """Raised when live mode is selected but no API key is configured."""


class LiveProvider(LlmProvider):
    """Anthropic-backed extraction provider."""

    source = "anthropic"

    def __init__(self, api_key: str = "", model: str = "") -> None:
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.anthropic_model

    def extract(self, sha256: str, lines: list[OcrLine]) -> ExtractionResult:
        if not self.api_key:
            raise MissingApiKeyError(
                "LLM_MODE=live requires ANTHROPIC_API_KEY in .env. "
                "Set it, or switch to LLM_MODE=fixture."
            )
        numbered = "\n".join(f"{line.line_no}: {line.text}" for line in lines)
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "system": _SYSTEM,
            "messages": [
                {"role": "user", "content": f"OCR lines:\n{numbered}\n\nReturn JSON."}
            ],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        resp = httpx.post(_API_URL, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        body = resp.json()
        text = "".join(
            block.get("text", "")
            for block in body.get("content", [])
            if block.get("type") == "text"
        )
        data = json.loads(text)
        return ExtractionResult.model_validate(data)
