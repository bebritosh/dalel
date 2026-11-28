"""Generate realistic-looking synthetic eval cases: phone photos of fiscal receipts.

Everything is invented (shops, BINs, people, amounts); no real receipt is used.
Compared with scripts/make_synthetic.py these cases look like what a user
actually uploads:

- Kazakhstan fiscal receipt layout on narrow thermal paper (monospace font):
  BIN, cash-register ids (ZNM/RNM), shift/receipt numbers, fiscal sign, VAT
  line, QR block.
- Distractor amounts next to the total: discount, VAT, cash tendered, change,
  per-line subtotals. The extractor must pick ИТОГО, not the largest number.
- Photo conditions: perspective, table background, uneven light / shadow,
  a fold line, slight defocus, JPEG compression.
- WhatsApp chats with several messages, a media placeholder and a polite
  seller reply before the refusal.

Outputs: eval/cases/case-010..case-015/{receipt.png,chat.txt} and the matching
entries in eval/gold.json (exact by construction, NOT OCR output). Existing
gold entries are kept.

Run:
    .venv/bin/python scripts/make_realistic.py
"""

from __future__ import annotations

import io
import json
import random
from datetime import date, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

CASES_DIR = Path("eval/cases")
GOLD_PATH = Path("eval/gold.json")
SEED = 20261126
FIRST_ID = 10
WIDTH_CHARS = 32


def _mono(size: int) -> ImageFont.FreeTypeFont:
    for candidate in (
        "/System/Library/Fonts/Supplemental/Courier New.ttf",  # macOS
        "/System/Library/Fonts/Menlo.ttc",
        "C:/Windows/Fonts/cour.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _money(kop: int) -> str:
    """Amount in tiyn -> '45 990,00'."""
    whole, frac = divmod(kop, 100)
    return f"{whole:,}".replace(",", " ") + f",{frac:02d}"


def _gold_amount(kop: int) -> str:
    whole, frac = divmod(kop, 100)
    return f"{whole}.{frac:02d}"


def _lr(left: str, right: str) -> str:
    """Left/right justified line on the thermal-paper width."""
    gap = max(1, WIDTH_CHARS - len(left) - len(right))
    return f"{left}{' ' * gap}{right}"


# photo kinds: photo-cash | photo-discount | photo-multi | photo-shadow |
#              photo-angle | photo-fold
SPECS = [
    dict(kind="photo-cash", seller="ТОО «Нур Электро»", bin="190340021187",
         addr="г. Алматы, ул. Жандосова 58", buyer="Айжан Сеитова",
         when=(2026, 10, 15, "14:22:07"), shift=214, no=118, cashier="Иманова А.",
         items=[("Микроволновка Breeze 20", 1, 4599000)], discount=0,
         pay="cash", tendered=5000000, product="микроволновку Breeze",
         gaps=(3, 3, 6), persp=0.05, shadow=0.25, fold=False, blur=0.6, jpeg=78),
    dict(kind="photo-discount", seller="ИП Ахметов Д.К.", bin="870512301456",
         addr="г. Астана, пр. Мангилик Ел 31", buyer="Олжас Бекенов",
         when=(2026, 9, 3, "19:47:31"), shift=88, no=2041, cashier="Ахметов Д.",
         items=[("Пылесос Storm X3", 1, 7499000), ("Мешки для пылесоса", 2, 199000)],
         discount=750000, pay="card", product="пылесос Storm",
         gaps=(5, 5, 9), persp=0.06, shadow=0.2, fold=False, blur=0.5, jpeg=75),
    dict(kind="photo-multi", seller="ТОО «Kazyna Retail»", bin="210840009932",
         addr="г. Шымкент, ул. Тауке хана 104", buyer="Камила Жунусова",
         when=(2026, 8, 22, "11:03:55"), shift=402, no=77, cashier="Ли Е.",
         items=[("Электрочайник Steam 1.7", 1, 1299000),
                ("Блендер Mix Pro", 1, 2349000),
                ("Тостер Crisp 2", 1, 1149000)],
         discount=0, pay="card", product="блендер Mix Pro",
         gaps=(2, 2, 7), persp=0.04, shadow=0.15, fold=False, blur=0.4, jpeg=80),
    dict(kind="photo-shadow", seller="ТОО «Арна Гаджет»", bin="160240017765",
         addr="г. Караганда, ул. Ерубаева 47", buyer="Даурен Касенов",
         when=(2026, 11, 2, "17:15:40"), shift=19, no=356, cashier="Сабитова Г.",
         items=[("Смарт-часы Pulse Fit", 1, 3990000)],
         discount=0, pay="cash", tendered=4000000, product="смарт-часы Pulse",
         gaps=(1, 1, 4), persp=0.05, shadow=0.55, fold=False, blur=0.6, jpeg=72),
    dict(kind="photo-angle", seller="ТОО «Табыс Home»", bin="200940031210",
         addr="г. Актобе, пр. Абилкайыр хана 63", buyer="Елена Ким",
         when=(2026, 7, 11, "12:38:02"), shift=145, no=903, cashier="Нурланова А.",
         items=[("Утюг Glide 2400", 1, 1899000)],
         discount=100000, pay="card", product="утюг Glide",
         gaps=(4, 4, 8), persp=0.13, shadow=0.2, fold=False, blur=0.7, jpeg=74),
    dict(kind="photo-fold", seller="ИП Жумабаева С.", bin="910303402318",
         addr="г. Павлодар, ул. Торайгырова 12", buyer="Арман Тулегенов",
         when=(2026, 6, 28, "10:05:19"), shift=61, no=1277, cashier="Жумабаева С.",
         items=[("Фен Breeze Air", 1, 1690000), ("Расческа", 1, 249000)],
         discount=0, pay="card", product="фен Breeze Air",
         gaps=(2, 3, 6), persp=0.07, shadow=0.3, fold=True, blur=0.8, jpeg=70),
]


def _receipt_lines(spec: dict, rng: random.Random) -> tuple[list[str], int]:
    y, m, d, hms = spec["when"]
    subtotal = sum(q * p for _, q, p in spec["items"])
    total = subtotal - spec["discount"]
    vat = round(total * 12 / 112)
    lines = [
        spec["seller"],
        f"БИН {spec['bin']}",
        spec["addr"],
        f"ЗНМ SWK{rng.randint(10**7, 10**8 - 1)}",
        f"РНМ {rng.randint(10**11, 10**12 - 1)}",
        "ФИСКАЛЬНЫЙ ЧЕК",
        "ПРОДАЖА",
        _lr(f"Смена № {spec['shift']}", f"Чек № {spec['no']}"),
        f"Кассир: {spec['cashier']}",
        "-" * WIDTH_CHARS,
    ]
    for idx, (name, qty, price) in enumerate(spec["items"], start=1):
        lines.append(f"{idx}. {name}")
        lines.append(_lr(f"  {qty} x {_money(price)}", f"= {_money(qty * price)}"))
    lines.append("-" * WIDTH_CHARS)
    if spec["discount"]:
        lines.append(_lr("Сумма:", _money(subtotal)))
        lines.append(_lr("Скидка:", f"-{_money(spec['discount'])}"))
    lines.append(_lr("ИТОГО:", _money(total)))
    if spec["pay"] == "cash":
        lines.append(_lr("Наличные:", _money(spec["tendered"])))
        lines.append(_lr("Сдача:", _money(spec["tendered"] - total)))
    else:
        lines.append(_lr("Банковская карта:", _money(total)))
    lines += [
        _lr("в т.ч. НДС 12%:", _money(vat)),
        f"ФП: {rng.randint(10**9, 10**10 - 1)}",
        f"Дата: {d:02d}.{m:02d}.{y} {hms}",
        "Валюта: KZT",
        "ОФД: ofd-demo.kz (демо)",
        "",  # QR block is drawn below the text
        "СПАСИБО ЗА ПОКУПКУ!",
    ]
    return lines, total


def _paper(lines: list[str], rng: random.Random) -> Image.Image:
    """Thermal paper strip with slightly uneven ink."""
    font = _mono(24)
    step = 34
    qr = 150
    width = 520
    height = 60 + step * len(lines) + qr + 40
    paper = Image.new("RGB", (width, height), (246, 244, 238))
    draw = ImageDraw.Draw(paper)
    y = 30
    for text in lines:
        if text == "":
            # Fake QR: random modules, no payload.
            x0 = (width - qr) // 2
            draw.rectangle((x0, y, x0 + qr, y + qr), fill=(246, 244, 238))
            cell = qr // 25
            for cy in range(25):
                for cx in range(25):
                    corner = (cx < 7 and cy < 7) or (cx > 17 and cy < 7) or (cx < 7 and cy > 17)
                    on = rng.random() < 0.5 if not corner else (
                        cx % 6 == 0 or cy % 6 == 0 or (2 <= cx % 18 <= 4 and 2 <= cy % 18 <= 4)
                    )
                    if on:
                        draw.rectangle((x0 + cx * cell, y + cy * cell,
                                        x0 + cx * cell + cell - 1, y + cy * cell + cell - 1),
                                       fill=(30, 30, 30))
            y += qr + 10
            continue
        ink = rng.randint(25, 70)
        draw.text((28, y), text, fill=(ink, ink, ink + 5), font=font)
        y += step
    return paper


def _table(size: tuple[int, int], rng: random.Random) -> Image.Image:
    """Wood-like table surface: horizontal grain plus noise."""
    w, h = size
    base = Image.new("RGB", size, (120, 86, 58))
    draw = ImageDraw.Draw(base)
    for yy in range(0, h, 3):
        shade = rng.randint(-18, 18)
        draw.line((0, yy, w, yy + rng.randint(-6, 6)),
                  fill=(120 + shade, 86 + shade, 58 + shade // 2), width=3)
    grain = Image.frombytes("L", size, rng.randbytes(w * h)).convert("RGB")
    return Image.blend(base, grain, 0.06).filter(ImageFilter.GaussianBlur(1.2))


def _perspective_coeffs(src: list[tuple[float, float]], dst: list[tuple[float, float]]):
    """Coefficients for Image.transform(PERSPECTIVE) mapping dst -> src."""
    rows = []
    for (x, y), (u, v) in zip(dst, src):
        rows.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        rows.append([0, 0, 0, x, y, 1, -v * x, -v * y])
    b = [c for pt in src for c in pt]
    return _solve(rows, b)


def _solve(a: list[list[float]], b: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting (keeps numpy out of deps)."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        m[col], m[piv] = m[piv], m[col]
        for r in range(n):
            if r != col:
                k = m[r][col] / m[col][col]
                m[r] = [x - k * y for x, y in zip(m[r], m[col])]
    return [m[i][n] / m[i][i] for i in range(n)]


def _photo(paper: Image.Image, spec: dict, rng: random.Random) -> Image.Image:
    pw, ph = paper.size
    if spec["fold"]:
        # Fold across the middle: darker crease and a lighter ridge.
        fold = Image.new("L", paper.size, 0)
        fd = ImageDraw.Draw(fold)
        fy = int(ph * 0.47)
        fd.rectangle((0, fy - 3, pw, fy + 3), fill=90)
        fold = fold.filter(ImageFilter.GaussianBlur(4))
        paper = Image.composite(Image.new("RGB", paper.size, (150, 148, 140)), paper, fold)

    margin = 140
    canvas_w, canvas_h = pw + 2 * margin, ph + 2 * margin
    canvas = _table((canvas_w, canvas_h), rng)
    canvas.paste(paper, (margin, margin))

    # Perspective: move the paper corners inwards by a random fraction.
    p = spec["persp"]
    corners = [(margin, margin), (margin + pw, margin), (margin + pw, margin + ph), (margin, margin + ph)]
    jitter = [
        (rng.uniform(0, p) * pw, rng.uniform(0, p * 0.5) * ph),
        (-rng.uniform(0, p) * pw, rng.uniform(0, p * 0.3) * ph),
        (-rng.uniform(0, p * 0.4) * pw, -rng.uniform(0, p * 0.3) * ph),
        (rng.uniform(0, p * 0.4) * pw, -rng.uniform(0, p * 0.5) * ph),
    ]
    dst = [(x + dx, y + dy) for (x, y), (dx, dy) in zip(corners, jitter)]
    coeffs = _perspective_coeffs(corners, dst)
    photo = canvas.transform(canvas.size, Image.PERSPECTIVE, coeffs, Image.BICUBIC,
                             fillcolor=(110, 80, 55))

    # Uneven light: a soft dark band (phone/hand shadow) plus a vignette.
    shade = Image.new("L", photo.size, 0)
    sd = ImageDraw.Draw(shade)
    sx = rng.randint(int(canvas_w * 0.45), int(canvas_w * 0.8))
    sd.polygon([(sx, 0), (canvas_w, 0), (canvas_w, canvas_h), (sx - 160, canvas_h)],
               fill=int(255 * spec["shadow"]))
    shade = shade.filter(ImageFilter.GaussianBlur(70))
    photo = Image.composite(Image.new("RGB", photo.size, (20, 18, 15)), photo, shade)
    vignette = Image.new("L", photo.size, 0)
    ImageDraw.Draw(vignette).ellipse((-canvas_w * 0.3, -canvas_h * 0.2,
                                      canvas_w * 1.3, canvas_h * 1.2), fill=255)
    vignette = vignette.filter(ImageFilter.GaussianBlur(120))
    photo = Image.composite(photo, Image.new("RGB", photo.size, (40, 32, 26)), vignette)

    photo = photo.rotate(rng.uniform(-2.5, 2.5), resample=Image.BICUBIC,
                         fillcolor=(100, 74, 50))
    photo = photo.filter(ImageFilter.GaussianBlur(spec["blur"]))
    sensor = Image.frombytes("L", photo.size, rng.randbytes(photo.size[0] * photo.size[1]))
    photo = Image.blend(photo, sensor.convert("RGB"), 0.035)

    # Phone JPEG round trip, stored as PNG so the eval harness reads it as-is.
    buf = io.BytesIO()
    photo.save(buf, "JPEG", quality=spec["jpeg"])
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def _chat(spec: dict) -> tuple[str, dict]:
    y, m, d, _ = spec["when"]
    buy = date(y, m, d)
    g_contact, g_reply, g_refuse = spec["gaps"]
    d_contact = buy + timedelta(days=g_contact)
    d_reply = buy + timedelta(days=g_reply)
    d_refuse = buy + timedelta(days=g_refuse)
    d_photo = d_reply + timedelta(days=1) if d_reply + timedelta(days=1) < d_refuse else d_reply
    shop = spec["seller"].replace("ТОО", "").replace("ИП", "").strip(" «»")
    buyer = spec["buyer"]

    def f(dt: date, hm: str) -> str:
        return f"{dt.day:02d}.{dt.month:02d}.{dt.year}, {hm}"

    chat = (
        f"{f(d_contact, '09:12')} - {buyer}: Добрый день! {d:02d}.{m:02d} купил(а) у вас "
        f"{spec['product']}, сегодня перестал(а) работать 😕\n"
        f"{f(d_contact, '09:13')} - {buyer}: Чек сохранил(а), могу прислать фото\n"
        f"{f(d_reply, '13:40')} - {shop}: Здравствуйте! Пришлите, пожалуйста, фото чека "
        f"и видео, как проявляется дефект\n"
        f"{f(d_photo, '18:02')} - {buyer}: <Медиафайл отсутствует>\n"
        f"{f(d_photo, '18:03')} - {buyer}: Вот чек и видео. Прошу вернуть деньги или заменить товар\n"
        f"{f(d_refuse, '11:25')} - {shop}: Мы посмотрели видео. Это механическое "
        f"повреждение, случай не гарантийный, в возврате отказываем.\n"
        f"{f(d_refuse, '11:31')} - {buyer}: Повреждений не было, я буду писать претензию\n"
    )
    events = {
        "contact": d_contact.isoformat(),
        "reply": d_reply.isoformat(),
        "refusal": d_refuse.isoformat(),
    }
    return chat, events


def build() -> None:
    rng = random.Random(SEED)
    gold = json.loads(GOLD_PATH.read_text(encoding="utf-8")) if GOLD_PATH.exists() else {}
    for idx, spec in enumerate(SPECS, start=FIRST_ID):
        case_id = f"case-{idx:03d}"
        out = CASES_DIR / case_id
        out.mkdir(parents=True, exist_ok=True)
        lines, total = _receipt_lines(spec, rng)
        _photo(_paper(lines, rng), spec, rng).save(out / "receipt.png")
        chat, events = _chat(spec)
        (out / "chat.txt").write_text(chat, encoding="utf-8")
        y, m, d, _ = spec["when"]
        gold[case_id] = {
            "kind": spec["kind"],
            "seller": spec["seller"],
            "purchase_date": f"{y}-{m:02d}-{d:02d}",
            "total_amount": _gold_amount(total),
            "currency": "KZT",
            "items": [name for name, _, _ in spec["items"]],
            "events": events,
        }
        print(f"wrote {out}  ({spec['kind']}, total {_money(total)})")
    GOLD_PATH.write_text(json.dumps(gold, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"updated {GOLD_PATH}")


if __name__ == "__main__":
    build()
