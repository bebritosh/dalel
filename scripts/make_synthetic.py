"""Generate fictional synthetic eval cases (Pillow only, deterministic).

Outputs (all invented data, no real people or shops):
    eval/cases/case-001..case-009/receipt.png
    eval/cases/case-001..case-009/chat.txt
    eval/gold.json   - ground truth per case (written by the generator, so
                       it is exact by construction; it is NOT OCR output)

Run:
    python scripts/make_synthetic.py
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

CASES_DIR = Path("eval/cases")
GOLD_PATH = Path("eval/gold.json")
SEED = 20261129


def _font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",  # macOS
        "/System/Library/Fonts/Helvetica.ttc",  # macOS
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _money(value: int) -> str:
    """Format an integer amount as '1 249 990,00' (thin-free plain spaces)."""
    return f"{value:,}".replace(",", " ") + ",00"


def _amount_gold(value: int) -> str:
    return f"{value}.00"


# kind: clean | tilt | hard-glare | hard-blur | hard-small
SPECS = [
    dict(kind="clean", seller="ТОО «Алем Техно»", addr="г. Астана, ул. Сейфуллина 12",
         buyer="Дана Касымова", date=(2026, 3, 14), time="11:05", no="004512",
         items=[("Ноутбук Nova 15", 1, 389900)], chat_gap=(1, 3, 6),
         product="ноутбук Nova"),
    dict(kind="clean", seller="ИП Бекова", addr="г. Шымкент, мкр. Нурсат 7",
         buyer="Руслан Омаров", date=(2026, 6, 2), time="16:48", no="000087",
         items=[("Пылесос Vortex 2000", 1, 54990), ("Фильтр HEPA", 2, 4500)],
         chat_gap=(2, 4, 8), product="пылесос Vortex"),
    dict(kind="clean", seller="ТОО «Сары Маркет»", addr="г. Караганда, пр. Бухар-жырау 40",
         buyer="Айгуль Нуркенова", date=(2026, 9, 21), time="09:30", no="018233",
         items=[("Наушники Pulse BT", 1, 27990)], chat_gap=(1, 2, 5),
         product="наушники Pulse"),
    dict(kind="tilt", seller="ТОО «Дала Моторс»", addr="г. Актау, 15 мкр. д. 3",
         buyer="Тимур Жаксылыков", date=(2026, 1, 18), time="13:20", no="002901",
         items=[("Шины зимние R17", 4, 61500)], chat_gap=(3, 5, 9),
         product="шины", angle=2.5, noise=18),
    dict(kind="tilt", seller="ТОО «Жулдыз Бытовая техника»", addr="г. Павлодар, ул. Ломова 55",
         buyer="Салтанат Ермекова", date=(2026, 4, 9), time="18:02", no="077410",
         items=[("Стиральная машина Aqua 7", 1, 214500)], chat_gap=(1, 4, 7),
         product="стиральная машина", angle=-3.0, noise=24),
    dict(kind="tilt", seller="ИП Нурлан Сериков", addr="г. Атырау, ул. Азаттык 21",
         buyer="Мария Ли", date=(2026, 8, 30), time="12:15", no="000342",
         items=[("Смартфон Orbit S5", 1, 159000)], chat_gap=(2, 3, 10),
         product="смартфон Orbit", angle=1.5, noise=30),
    dict(kind="hard-glare", seller="ТОО «Арай Электроникс»", addr="г. Алматы, ул. Розыбакиева 99",
          buyer="Ерлан Токтаров", date=(2026, 10, 3), time="15:41", no="031775",
          items=[("Планшет Slate 10", 1, 119990)], chat_gap=(1, 5, 8),
          product="планшет Slate", angle=-1.0, noise=12),
    dict(kind="hard-blur", seller="ТОО «Кемел Трейд»", addr="г. Костанай, ул. Баймагамбетова 9",
         buyer="Гульнара Сабитова", date=(2026, 5, 12), time="10:10", no="009058",
         items=[("Холодильник Frost 300", 1, 342000)], chat_gap=(2, 4, 6),
         product="холодильник Frost", angle=1.0, noise=10),
    dict(kind="hard-small", seller="ТОО «Берекет Групп»", addr="г. Семей, ул. Найманбаева 31",
         buyer="Асхат Мусин", date=(2026, 7, 7), time="19:37", no="055126",
         items=[("Кофемашина Aroma One", 1, 87900), ("Чехол", 1, 3200)],
         chat_gap=(1, 3, 5), product="кофемашина Aroma", angle=-1.5, noise=14),
]


def _receipt_lines(spec: dict) -> tuple[list[str], int]:
    y, m, d = spec["date"]
    total = sum(q * p for _, q, p in spec["items"])
    lines = [spec["seller"], spec["addr"], f"Чек № {spec['no']}",
             f"Дата: {d:02d}.{m:02d}.{y} {spec['time']}", "-" * 32]
    for name, qty, price in spec["items"]:
        lines.append(name)
        lines.append(f"{qty} шт x {_money(price)}")
    lines += ["-" * 32, f"ИТОГО: {_money(total)} KZT", "Оплата: карта",
              "Спасибо за покупку!"]
    return lines, total


def _render(lines: list[str], spec: dict, rng: random.Random) -> Image.Image:
    kind = spec["kind"]
    size = 12 if kind == "hard-small" else 28
    step = int(size * 2.3) if kind != "hard-small" else int(size * 2.0)
    font = _font(size)
    width = 760 if kind != "hard-small" else 520
    height = 80 + step * len(lines) + 60
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    for i, text in enumerate(lines):
        draw.text((48, 50 + i * step), text, fill="black", font=font)

    if kind == "hard-glare":
        # Soft white blob over the middle of the receipt (flash reflection).
        glare = Image.new("L", image.size, 0)
        gd = ImageDraw.Draw(glare)
        cx, cy = int(width * 0.60), int(height * 0.60)  # over the ИТОГО line
        gd.ellipse((cx - 230, cy - 90, cx + 230, cy + 90), fill=255)
        glare = glare.filter(ImageFilter.GaussianBlur(30))
        image = Image.composite(Image.new("RGB", image.size, "white"), image, glare)
        # Mild grey cast so the glare edge is not a pure white cliff.
        image = Image.blend(image, Image.new("RGB", image.size, (200, 200, 200)), 0.12)
    if kind == "hard-blur":
        image = image.filter(ImageFilter.GaussianBlur(2.3))

    noise = spec.get("noise", 0)
    if noise:
        grain = Image.frombytes(
            "L", image.size, rng.randbytes(image.size[0] * image.size[1])
        ).convert("RGB")
        # Blend towards random grain: darkens/lightens pixels unevenly.
        image = Image.blend(image, grain, noise / 255)
    angle = spec.get("angle", 0)
    if angle:
        image = image.rotate(angle, resample=Image.BICUBIC, expand=True,
                             fillcolor=(235, 235, 235))
    return image


def _chat(spec: dict) -> tuple[str, dict]:
    from datetime import date, timedelta

    y, m, d = spec["date"]
    buy = date(y, m, d)
    g1, g2, g3 = spec["chat_gap"]
    d_contact = buy + timedelta(days=g1)
    d_reply = d_contact
    d_photo = buy + timedelta(days=g2)
    d_refuse = buy + timedelta(days=g3)
    shop = spec["seller"].replace("ТОО", "").replace("ИП", "").strip(" «»")
    buyer = spec["buyer"]

    def f(dt: date, hm: str) -> str:
        return f"{dt.day:02d}.{dt.month:02d}.{dt.year}, {hm}"

    chat = (
        f"{f(d_contact, '10:15')} - {buyer}: Здравствуйте! Купил у вас {spec['product']}, "
        f"товар неисправен.\n"
        f"{f(d_reply, '11:40')} - {shop}: Добрый день. Пришлите фото дефекта.\n"
        f"{f(d_photo, '09:05')} - {buyer}: Отправляю фото. Прошу вернуть деньги.\n"
        f"{f(d_refuse, '16:20')} - {shop}: К сожалению, вернуть деньги не можем, "
        f"случай не гарантийный.\n"
    )
    events = {"contact": d_contact.isoformat(), "refusal": d_refuse.isoformat()}
    return chat, events


def build() -> None:
    rng = random.Random(SEED)
    gold: dict[str, dict] = {}
    for idx, spec in enumerate(SPECS, start=1):
        case_id = f"case-{idx:03d}"
        out = CASES_DIR / case_id
        out.mkdir(parents=True, exist_ok=True)
        lines, total = _receipt_lines(spec)
        image = _render(lines, spec, rng)
        image.save(out / "receipt.png")
        chat, events = _chat(spec)
        (out / "chat.txt").write_text(chat, encoding="utf-8")
        y, m, d = spec["date"]
        gold[case_id] = {
            "kind": spec["kind"],
            "seller": spec["seller"],
            "purchase_date": f"{y}-{m:02d}-{d:02d}",
            "total_amount": _amount_gold(total),
            "currency": "KZT",
            "items": [name for name, _, _ in spec["items"]],
            "events": events,
        }
        print(f"wrote {out}  ({spec['kind']}, total {total})")
    GOLD_PATH.write_text(
        json.dumps(gold, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {GOLD_PATH}")


if __name__ == "__main__":
    build()
