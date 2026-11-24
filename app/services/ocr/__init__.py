"""OCR layer: engines that turn a document into lines with bounding boxes."""

from app.services.ocr.base import OcrEngine, OcrLineData
from app.services.ocr.factory import get_ocr_engine, run_ocr

__all__ = ["OcrEngine", "OcrLineData", "get_ocr_engine", "run_ocr"]
