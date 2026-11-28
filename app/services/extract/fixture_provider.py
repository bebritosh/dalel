"""Fixture extraction provider: reads saved LLM responses, works offline."""

from __future__ import annotations

import json
from pathlib import Path

from app.models import OcrLine
from app.services.extract.base import LlmProvider
from app.services.extract.schema import ExtractionResult

FIXTURES_DIR = Path("eval/fixtures")


class FixtureProvider(LlmProvider):
    """Return a pre-saved extraction response keyed by document sha256.

    Fixtures are real captured live responses, except demo placeholders which
    are named with a 'handmade_' prefix and documented as such in the README.
    """

    source = "fixture"

    def __init__(self, fixtures_dir: Path | None = None) -> None:
        self.fixtures_dir = fixtures_dir or FIXTURES_DIR

    def has_fixture(self, sha256: str) -> bool:
        """True if an extraction fixture (real or handmade) exists for sha256."""
        return any(
            (self.fixtures_dir / name).exists()
            for name in (f"{sha256}.json", f"handmade_{sha256}.json")
        )

    def extract(self, sha256: str, lines: list[OcrLine]) -> ExtractionResult:
        # Real captured live responses are stored as "{sha}.json". Handmade demo
        # placeholders use the "handmade_" prefix (documented in the README) so
        # they are never passed off as real recognition output.
        candidates = [
            self.fixtures_dir / f"{sha256}.json",
            self.fixtures_dir / f"handmade_{sha256}.json",
        ]
        for path in candidates:
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                return ExtractionResult.model_validate(data)
        raise FileNotFoundError(
            f"No extraction fixture for sha256={sha256}. "
            f"Expected one of: {', '.join(str(c) for c in candidates)}."
        )
