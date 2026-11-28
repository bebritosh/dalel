"""Tesseract OCR engine (used only when Tesseract is installed).

Produces real per-line bounding boxes via pytesseract's image_to_data. This is
wired but optional: the pipeline defaults to the fixture engine. Enable with
OCR_ENGINE=tesseract once Tesseract is installed (see HANDOFF.md).
"""

from __future__ import annotations

import re

from pathlib import Path

from app.services.ocr.base import OcrEngine, OcrLineData
from app.services.ocr.pdf import extract_pdf_text_lines, rasterize_pdf
from app.services.ocr.preprocess import preprocess_image


# Legal-form prefix read with Latin look-alikes: "TOO «Нур»" -> "ТОО «Нур»".
_LEGAL_FORM = re.compile(r"^(?:[TТ][OoОо0]{2}|[AА][OО0])(?=\s|«|\"|$)")


def _fix_legal_form(text: str) -> str:
    """Map a Latin-homoglyph ТОО/АО at the start of a line to Cyrillic."""
    m = _LEGAL_FORM.match(text)
    if not m:
        return text
    word = m.group(0)
    cyr = "ТОО" if len(word) == 3 else "АО"
    return cyr + text[len(word):]


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

    @staticmethod
    def _fix_currency_code(pytesseract, image, data: dict) -> None:
        """Cross-check the currency code with an eng-only pass.

        With rus+eng, Tesseract often reads "KZT" as Cyrillic look-alikes
        ("КИТ", "КТ", "КРТ"). A Latin-only pass reads it reliably, so when it
        sees a standalone KZT word, the overlapping primary word is replaced by
        what that second real OCR pass read (nothing is invented).
        """
        latin = pytesseract.image_to_data(
            image, lang="eng", output_type=pytesseract.Output.DICT
        )
        def box(d: dict, k: int) -> tuple[int, int, int, int]:
            return (d["left"][k], d["top"][k],
                    d["left"][k] + d["width"][k], d["top"][k] + d["height"][k])

        def iou(a: tuple, b: tuple) -> float:
            w = min(a[2], b[2]) - max(a[0], b[0])
            h = min(a[3], b[3]) - max(a[1], b[1])
            if w <= 0 or h <= 0:
                return 0.0
            inter = w * h
            area = lambda r: (r[2] - r[0]) * (r[3] - r[1])  # noqa: E731
            return inter / (area(a) + area(b) - inter)

        for j, word in enumerate(latin["text"]):
            if (word or "").strip().upper() != "KZT":
                continue
            best, best_iou = None, 0.3  # require a real overlap, not containment
            for i, text in enumerate(data["text"]):
                if (text or "").strip():
                    score = iou(box(latin, j), box(data, i))
                    if score > best_iou:
                        best, best_iou = i, score
            if best is not None:
                data["text"][best] = "KZT"

    def _recognize_image(self, file_path: Path, page: int = 0) -> list[OcrLineData]:
        pytesseract = self._pytesseract()
        image = preprocess_image(file_path)
        data = pytesseract.image_to_data(
            # psm 6 (single uniform block) keeps a receipt row together: with
            # the default psm 3 the right-aligned amount column ("ИТОГО: ...
            # 45 990,00") became a separate block on phone photos.
            image, lang=self.langs, config="--psm 6", output_type=pytesseract.Output.DICT
        )
        if "rus" in self.langs:
            self._fix_currency_code(pytesseract, image, data)
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
                    text=_fix_legal_form(" ".join(g["words"])),
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
