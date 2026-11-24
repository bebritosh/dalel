"""Fixture OCR engine.

IMPORTANT (honesty): the *.layout.json files are the synthetic generator's
ground-truth layout for a document, NOT the output of a real OCR run. They let
the pipeline and the demo work offline and deterministically. A real OCR run is
provided by TesseractEngine and is used only when Tesseract is installed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.services.ocr.base import OcrEngine, OcrLineData

FIXTURES_DIR = Path("eval/fixtures")


class FixtureOcrEngine(OcrEngine):
    """Return OCR lines from a committed layout fixture keyed by file sha256."""

    def __init__(self, fixtures_dir: Path | None = None) -> None:
        self.fixtures_dir = fixtures_dir or FIXTURES_DIR

    def recognize(self, file_path: Path, mime_type: str) -> list[OcrLineData]:
        content = Path(file_path).read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        layout_path = self.fixtures_dir / f"{digest}.layout.json"
        if not layout_path.exists():
            raise FileNotFoundError(
                f"No OCR layout fixture for sha256={digest}. "
                f"Expected {layout_path}."
            )
        data = json.loads(layout_path.read_text(encoding="utf-8"))
        lines: list[OcrLineData] = []
        for item in data.get("lines", []):
            bbox = item.get("bbox", [0, 0, 0, 0])
            lines.append(
                OcrLineData(
                    line_no=int(item["line_no"]),
                    text=str(item["text"]),
                    bbox_x=int(bbox[0]),
                    bbox_y=int(bbox[1]),
                    bbox_w=int(bbox[2]),
                    bbox_h=int(bbox[3]),
                    page=int(item.get("page", 0)),
                )
            )
        return lines
