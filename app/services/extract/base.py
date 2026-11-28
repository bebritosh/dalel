"""LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import OcrLine
from app.services.extract.schema import ExtractionResult


class LlmProvider(ABC):
    """Abstract extraction provider. Returns values and line_ids only."""

    # Provenance label stored on the document: fixture | openai | anthropic | rules.
    source: str = ""

    @abstractmethod
    def extract(self, sha256: str, lines: list[OcrLine]) -> ExtractionResult:
        """Extract fields for a document identified by sha256 and its OCR lines."""
        raise NotImplementedError
