"""PDF handling: prefer embedded text, otherwise rasterize pages.

Returns either text lines (when the PDF has a text layer) or rendered page
images for a downstream image OCR engine.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF

from app.services.ocr.base import OcrLineData


def extract_pdf_text_lines(file_path: Path) -> list[OcrLineData]:
    """Extract text lines with bounding boxes from a PDF's text layer.

    Returns an empty list if the PDF has no usable embedded text (scanned PDF),
    in which case the caller should rasterize and run image OCR instead.
    """
    lines: list[OcrLineData] = []
    line_no = 0
    with fitz.open(file_path) as doc:
        for page_index, page in enumerate(doc):
            data = page.get_text("dict")
            for block in data.get("blocks", []):
                for line in block.get("lines", []):
                    text = "".join(
                        span.get("text", "") for span in line.get("spans", [])
                    ).strip()
                    if not text:
                        continue
                    x0, y0, x1, y1 = line.get("bbox", (0, 0, 0, 0))
                    lines.append(
                        OcrLineData(
                            line_no=line_no,
                            text=text,
                            bbox_x=int(x0),
                            bbox_y=int(y0),
                            bbox_w=int(x1 - x0),
                            bbox_h=int(y1 - y0),
                            page=page_index,
                        )
                    )
                    line_no += 1
    return lines


def rasterize_pdf(file_path: Path, dpi: int = 200) -> list[Path]:
    """Render each PDF page to a PNG next to the source; return the image paths."""
    out_paths: list[Path] = []
    with fitz.open(file_path) as doc:
        for page_index, page in enumerate(doc):
            pix = page.get_pixmap(dpi=dpi)
            out = Path(file_path).with_suffix("")
            img_path = out.parent / f"{out.name}_p{page_index}.png"
            pix.save(img_path)
            out_paths.append(img_path)
    return out_paths
