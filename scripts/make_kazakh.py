"""Generate synthetic eval cases with Kazakh-language fiscal receipts.

Everything is invented (shops, BINs, people, amounts); no real receipt is used.
Reuses the paper/photo pipeline of scripts/make_realistic.py, but the receipt
text is in Kazakh: ЖШС (= ТОО), БСН (= БИН), «ЖИЫНЫ»/«БАРЛЫҒЫ» (= ИТОГО),
«Қолма-қол»/«Қайтарым» (cash/change), «оның ішінде ҚҚС» (VAT), «Күні» (date).
Distractor amounts (cash tendered, subtotal before discount, VAT) are kept so
the extractor must pick the total line, not the largest number.

case-016 has a Russian chat; case-017 has a Kazakh chat (contact, a polite
seller reply, then a refusal in Kazakh) for rules/chat_events.yaml.

Outputs: eval/cases/case-016..case-017/{receipt.png,chat.txt} and the matching
entries in eval/gold.json (exact by construction, NOT OCR output). Existing
gold entries are kept.

Run:
    .venv/bin/python scripts/make_kazakh.py
"""

from __future__ import annotations

import json
import random
from datetime import date, timedelta

import make_realistic as mr

SEED = 20261127
FIRST_ID = 16

SPECS = [
    dict(kind="photo-kk-cash", seller="ЖШС «Алтын Техника»", shop="Алтын Техника",
         bin="200540018834", addr="Алматы қ., Абай даңғ. 150", buyer="Нұрлан Әбдіров",
         when=(2026, 10, 21, "16:08:44"), shift=57, no=412, cashier="Төлеуова Ә.",
         items=[("Шаңсорғыш Vortex 5", 1, 5299000)], discount=0,
         pay="cash", tendered=6000000, product="пылесос Vortex",
         total_word="ЖИЫНЫ:", currency_line="Валюта: KZT",
         gaps=(2, 3, 6), persp=0.05, shadow=0.2, fold=False, blur=0.5, jpeg=78),
    dict(kind="photo-kk-card", seller="ЖК Сәрсенбаев Қ.Т.", shop="Сәрсенбаев",
         bin="880214300527", addr="Астана қ., Қабанбай батыр даңғ. 21", buyer="Гүлнар Омарова",
         when=(2026, 9, 14, "12:51:09"), shift=133, no=1876, cashier="Сәрсенбаев Қ.",
         items=[("Электр шәйнегі Aqua 1.7", 1, 1499000), ("Тостер Crisp 2", 1, 1149000)],
         discount=200000, pay="card", product="электрочайник Aqua", product_kk="Aqua электр шәйнегін",
         total_word="БАРЛЫҒЫ:", currency_line="Валюта: теңге",
         chat_lang="kk", gaps=(4, 4, 8), persp=0.08, shadow=0.3, fold=False, blur=0.6, jpeg=74),
]


def _receipt_lines(spec: dict, rng: random.Random) -> tuple[list[str], int]:
    lr, money = mr._lr, mr._money
    y, m, d, hms = spec["when"]
    subtotal = sum(q * p for _, q, p in spec["items"])
    total = subtotal - spec["discount"]
    vat = round(total * 12 / 112)
    lines = [
        spec["seller"],
        f"БСН {spec['bin']}",
        spec["addr"],
        f"ЗНМ SWK{rng.randint(10**7, 10**8 - 1)}",
        f"РНМ {rng.randint(10**11, 10**12 - 1)}",
        "ФИСКАЛДЫҚ ЧЕК",
        "САТУ",
        lr(f"Ауысым № {spec['shift']}", f"Чек № {spec['no']}"),
        f"Кассир: {spec['cashier']}",
        "-" * mr.WIDTH_CHARS,
    ]
    for idx, (name, qty, price) in enumerate(spec["items"], start=1):
        lines.append(f"{idx}. {name}")
        lines.append(lr(f"  {qty} x {money(price)}", f"= {money(qty * price)}"))
    lines.append("-" * mr.WIDTH_CHARS)
    if spec["discount"]:
        lines.append(lr("Сома:", money(subtotal)))
        lines.append(lr("Жеңілдік:", f"-{money(spec['discount'])}"))
    lines.append(lr(spec["total_word"], money(total)))
    if spec["pay"] == "cash":
        lines.append(lr("Қолма-қол:", money(spec["tendered"])))
        lines.append(lr("Қайтарым:", money(spec["tendered"] - total)))
    else:
        lines.append(lr("Банк картасы:", money(total)))
    lines += [
        lr("оның ішінде ҚҚС 12%:", money(vat)),
        f"ФБ: {rng.randint(10**9, 10**10 - 1)}",
        f"Күні: {d:02d}.{m:02d}.{y} {hms}",
        spec["currency_line"],
        "ФДО: ofd-demo.kz (демо)",
        "",  # QR block is drawn below the text
        "САТЫП АЛҒАНЫҢЫЗҒА РАХМЕТ!",
    ]
    return lines, total


def _chat_kk(spec: dict) -> tuple[str, dict]:
    """Kazakh WhatsApp chat with the same event dates as mr._chat()."""
    y, m, d, _ = spec["when"]
    buy = date(y, m, d)
    g_contact, g_reply, g_refuse = spec["gaps"]
    d_contact = buy + timedelta(days=g_contact)
    d_reply = buy + timedelta(days=g_reply)
    d_refuse = buy + timedelta(days=g_refuse)
    shop, buyer = spec["shop"], spec["buyer"]

    def f(dt: date, hm: str) -> str:
        return f"{dt.day:02d}.{dt.month:02d}.{dt.year}, {hm}"

    chat = (
        f"{f(d_contact, '09:12')} - {buyer}: Сәлеметсіз бе! {d:02d}.{m:02d} сізден "
        f"{spec['product_kk']} алдым, бүгін істемей қалды\n"
        f"{f(d_contact, '09:13')} - {buyer}: Чек сақталған, фотосын жібере аламын\n"
        f"{f(d_reply, '13:40')} - {shop}: Сәлеметсіз бе! Чектің фотосын және ақаудың "
        f"видеосын жіберіңізші\n"
        f"{f(d_reply, '18:03')} - {buyer}: Міне, чек пен видео. Ақшаны қайтаруыңызды "
        f"немесе тауарды ауыстыруыңызды сұраймын\n"
        f"{f(d_refuse, '11:25')} - {shop}: Видеоны қарадық. Бұл механикалық зақым, "
        f"кепілдікке жатпайды, ақшаны қайтара алмаймыз.\n"
        f"{f(d_refuse, '11:31')} - {buyer}: Зақым болған жоқ, мен шағым жазамын\n"
    )
    events = {
        "contact": d_contact.isoformat(),
        "reply": d_reply.isoformat(),
        "refusal": d_refuse.isoformat(),
    }
    return chat, events


def build() -> None:
    rng = random.Random(SEED)
    gold = json.loads(mr.GOLD_PATH.read_text(encoding="utf-8")) if mr.GOLD_PATH.exists() else {}
    for idx, spec in enumerate(SPECS, start=FIRST_ID):
        case_id = f"case-{idx:03d}"
        out = mr.CASES_DIR / case_id
        out.mkdir(parents=True, exist_ok=True)
        lines, total = _receipt_lines(spec, rng)
        mr._photo(mr._paper(lines, rng), spec, rng).save(out / "receipt.png")
        # _chat() strips ТОО/ИП from `seller`; pass the bare shop name instead.
        if spec.get("chat_lang") == "kk":
            chat, events = _chat_kk(spec)
        else:
            chat, events = mr._chat(dict(spec, seller=spec["shop"]))
        (out / "chat.txt").write_text(chat, encoding="utf-8")
        y, m, d, _ = spec["when"]
        gold[case_id] = {
            "kind": spec["kind"],
            "seller": spec["seller"],
            "purchase_date": f"{y}-{m:02d}-{d:02d}",
            "total_amount": mr._gold_amount(total),
            "currency": "KZT",
            "items": [name for name, _, _ in spec["items"]],
            "events": events,
        }
        print(f"wrote {out}  ({spec['kind']}, total {mr._money(total)})")
    mr.GOLD_PATH.write_text(json.dumps(gold, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"updated {mr.GOLD_PATH}")


if __name__ == "__main__":
    build()
