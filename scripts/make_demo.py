"""Generate one synthetic demo case and its offline fixtures.

Outputs (all synthetic, fully invented data):
    eval/cases/demo-001/receipt.png   - a rendered receipt image
    eval/cases/demo-001/chat.txt      - a WhatsApp-style export
    eval/fixtures/{sha}.layout.json   - generator ground-truth layout (NOT OCR)
    eval/fixtures/handmade_{sha}.json - handmade extraction response (NOT live LLM)

Run:
    python scripts/make_demo.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CASE_DIR = Path("eval/cases/demo-001")
FIX_DIR = Path("eval/fixtures")

RECEIPT_LINES = [
    "ТОО «Пример Электроникс»",
    "г. Алматы, пр. Абая 150",
    "Чек № 000123",
    "Дата: 05.11.2026 14:32",
    "Кассир: Иванова А.",
    "--------------------------------",
    "Смартфон X 128GB",
    "1 шт x 249 990,00",
    "--------------------------------",
    "ИТОГО: 249 990,00 KZT",
    "Оплата: карта",
    "Спасибо за покупку!",
]

CHAT = """06.11.2026, 10:15 - Арман Серіков: Здравствуйте! Вчера купил у вас смартфон X, экран мигает и сильно греется.
06.11.2026, 11:40 - Пример Электроникс: Добрый день. Пришлите фото дефекта, рассмотрим.
08.11.2026, 09:05 - Арман Серіков: Отправляю фото. Прошу вернуть деньги за товар.
09.11.2026, 16:20 - Пример Электроникс: К сожалению, вернуть деньги не можем, случай не гарантийный.
"""


def _font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in (
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def build() -> None:
    CASE_DIR.mkdir(parents=True, exist_ok=True)
    FIX_DIR.mkdir(parents=True, exist_ok=True)

    width, height = 760, 1040
    margin_x, start_y, step = 48, 60, 72
    font = _font(28)

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    layout_lines = []
    for i, text in enumerate(RECEIPT_LINES):
        y = start_y + i * step
        draw.text((margin_x, y), text, fill="black", font=font)
        left, top, right, bottom = draw.textbbox((margin_x, y), text, font=font)
        layout_lines.append(
            {
                "line_no": i,
                "text": text,
                "bbox": [int(left), int(top), int(right - left), int(bottom - top)],
                "page": 0,
            }
        )

    receipt_path = CASE_DIR / "receipt.png"
    image.save(receipt_path)
    (CASE_DIR / "chat.txt").write_text(CHAT, encoding="utf-8")

    content = receipt_path.read_bytes()
    sha = hashlib.sha256(content).hexdigest()

    layout = {"image": {"width": width, "height": height}, "lines": layout_lines}
    (FIX_DIR / f"{sha}.layout.json").write_text(
        json.dumps(layout, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    extraction = {
        "_source": "handmade_no_live_llm",
        "document_type": "receipt",
        "fields": {
            "seller_name": {
                "value": "ТОО «Пример Электроникс»",
                "line_ids": [0],
                "confidence": 0.95,
            },
            "purchase_date": {
                "value": "2026-11-05",
                "line_ids": [3],
                "confidence": 0.9,
            },
            "total_amount": {
                "value": "249990.00",
                "line_ids": [9],
                "confidence": 0.92,
            },
            "currency": {"value": "KZT", "line_ids": [9], "confidence": 0.85},
            "items": [
                {
                    "name": "Смартфон X 128GB",
                    "qty": 1,
                    "price": "249990.00",
                    "line_ids": [6, 7],
                }
            ],
        },
        "unreadable": ["warranty_period"],
    }
    (FIX_DIR / f"handmade_{sha}.json").write_text(
        json.dumps(extraction, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"receipt sha256 = {sha}")
    print(f"wrote {receipt_path}")
    print(f"wrote {CASE_DIR / 'chat.txt'}")
    print(f"wrote {FIX_DIR / f'{sha}.layout.json'}")
    print(f"wrote {FIX_DIR / f'handmade_{sha}.json'}")


if __name__ == "__main__":
    build()
