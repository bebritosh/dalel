"""Tesseract OCR engine (used only when Tesseract is installed).

Produces real per-line bounding boxes via pytesseract's image_to_data. This is
wired but optional: the pipeline defaults to the fixture engine. Enable with
OCR_ENGINE=tesseract once Tesseract is installed (see HANDOFF.md).
"""

from __future__ import annotations

from pathlib import Path

from app.services.ocr.base import OcrEngine, OcrLineData
from app.services.ocr.pdf import extract_pdf_text_lines, rasterize_pdf
from app.services.ocr.preprocess import preprocess_image


class TesseractEngine(OcrEngine):
    """Recognize images (and scanned PDFs) with Tesseract."""

    def __init__(self, langs: str = "rus+eng", tesseract_cmd: str = "") -> None:
        self.langs = langs
        self.tesseract_cmd = tesseract_cmd

    def _pytesseract(self):
        import pytesseract  # imported lazily so the dep isn't required otherwise

        if self.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
        return pytesseract

    def _recognize_image(self, file_path: Path, page: int = 0) -> list[OcrLineData]:
        pytesseract = self._pytesseract()
        image = preprocess_image(file_path)
        data = pytesseract.image_to_data(
            image, lang=self.langs, output_type=pytesseract.Output.DICT
        )
        # Group words into lines by (block_num, par_num, line_num).
        groups: dict[tuple[int, int, int], dict] = {}
        n = len(data["text"])
        for i in range(n):
            text = (data["text"][i] or "").strip()
            if not text:
                continue
            key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            g = groups.setdefault(
                key,
                {"words": [], "x": [], "y": [], "r": [], "b": []},
            )
            x, y, w, h = (
                data["left"][i],
                data["top"][i],
                data["width"][i],
                data["height"][i],
            )
            g["words"].append(text)
            g["x"].append(x)
            g["y"].append(y)
            g["r"].append(x + w)
            g["b"].append(y + h)

        lines: list[OcrLineData] = []
        for line_no, key in enumerate(sorted(groups)):
            g = groups[key]
            x0, y0 = min(g["x"]), min(g["y"])
            x1, y1 = max(g["r"]), max(g["b"])
            lines.append(
                OcrLineData(
                    line_no=line_no,
                    text=" ".join(g["words"]),
                    bbox_x=int(x0),
                    bbox_y=int(y0),
                    bbox_w=int(x1 - x0),
                    bbox_h=int(y1 - y0),
                    page=page,
                )
            )
        return lines

    def recognize(self, file_path: Path, mime_type: str) -> list[OcrLineData]:
        path = Path(file_path)
        if mime_type == "application/pdf":
            text_lines = extract_pdf_text_lines(path)
            if text_lines:
                return text_lines
            lines: list[OcrLineData] = []
            for page_index, img_path in enumerate(rasterize_pdf(path)):
                lines.extend(self._recognize_image(img_path, page=page_index))
            # Renumber across pages.
            for i, line in enumerate(lines):
                line.line_no = i
            return lines
        return self._recognize_image(path)
