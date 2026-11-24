"""OCR engine interface and line data structure."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class OcrLineData:
    """One recognized line with its bounding box, in image pixel coordinates."""

    line_no: int
    text: str
    bbox_x: int = 0
    bbox_y: int = 0
    bbox_w: int = 0
    bbox_h: int = 0
    page: int = 0


class OcrEngine(ABC):
    """Abstract OCR engine. Implementations return lines with bounding boxes."""

    @abstractmethod
    def recognize(self, file_path: Path, mime_type: str) -> list[OcrLineData]:
        """Recognize a document file into a list of OCR lines."""
        raise NotImplementedError
