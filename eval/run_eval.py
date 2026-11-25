"""One-command evaluation: real OCR (Tesseract) + extraction + claim guard.

Run:
    .venv/bin/python eval/run_eval.py [--mode rules|openai|auto|fixture] [--cases case-001 ...]

Per case it measures OCR-level recall (is the gold value anywhere in the OCR
text), extraction accuracy per field, grounding, hallucination rate, latency,
and whether the claim guard blocks a claim with a substituted amount.

Outputs: console table, eval/last_run.json (gitignored) and a committed
snapshot eval/results/<mode>-<YYYYMMDD-HHMM>.json.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from app.services.extract.normalize import (  # noqa: E402
    iter_dates,
    iter_numbers,
    normalize_date,
    normalize_number,
)

CASES_DIR = ROOT / "eval" / "cases"
GOLD_PATH = ROOT / "eval" / "gold.json"
RESULTS_DIR = ROOT / "eval" / "results"
LAST_RUN = ROOT / "eval" / "last_run.json"
FIELDS = ("seller", "date", "total", "currency", "item")


# --------------------------------------------------------------------------
# Pure metric functions (no Tesseract, no DB): covered by tests/test_eval_metrics.py
# --------------------------------------------------------------------------
def norm_text(text: str) -> str:
    """Casefold, drop quotes/punctuation, collapse whitespace."""
    text = re.sub(r"[«»\"'.,;:]", " ", text or "")
    return re.sub(r"\s+", " ", text).strip().casefold()


def match_seller(extracted: str | None, gold: str) -> bool:
    return bool(extracted) and norm_text(extracted) == norm_text(gold)


def match_date(extracted: str | None, gold: str) -> bool:
    if not extracted:
        return False
    d = normalize_date(extracted)
    return d is not None and d == normalize_date(gold)


def match_total(extracted: str | None, gold: str) -> bool:
    if not extracted:
        return False
    n = normalize_number(extracted)
    return n is not None and n == normalize_number(gold)


def match_currency(extracted: str | None, gold: str) -> bool:
    return bool(extracted) and extracted.strip().upper() == gold.strip().upper()


def item_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, norm_text(a), norm_text(b)).ratio()


def match_items(extracted: list[str], gold: list[str], threshold: float = 0.85) -> float:
    """Share of gold items that have a close-enough extracted item."""
    if not gold:
        return 1.0
    hits = sum(
        1 for g in gold if any(item_similarity(e, g) >= threshold for e in extracted)
    )
    return hits / len(gold)


def value_in_text(kind: str, value: str, text: str) -> bool:
    """Is a value (date | number | string) present anywhere in OCR text?"""
    if not value:
        return False
    if kind == "date":
        d = normalize_date(value)
        return d is not None and d in iter_dates(text)
    if kind == "number":
        n = normalize_number(value)
        return n is not None and n in iter_numbers(text)
    return norm_text(value) in norm_text(text)


def fuzzy_in_text(value: str, text: str, threshold: float = 0.85) -> bool:
    """Approximate string presence (for OCR recall of seller/item names)."""
    if value_in_text("string", value, text):
        return True
    needle = norm_text(value)
    hay = norm_text(text)
    n = len(needle)
    if not n or len(hay) < n:
        return False
    best = 0.0
    for i in range(0, len(hay) - n + 1):
        best = max(best, difflib.SequenceMatcher(None, needle, hay[i:i + n]).ratio())
        if best >= threshold:
            return True
    return False


def ocr_recall(gold: dict, text: str) -> dict[str, bool]:
    """Which gold values appear in the OCR text (OCR errors vs extraction errors)."""
    return {
        "seller": fuzzy_in_text(gold["seller"], text),
        "date": value_in_text("date", gold["purchase_date"], text),
        "total": value_in_text("number", gold["total_amount"], text),
        "currency": value_in_text("string", gold["currency"], text),
        "item": (
            sum(fuzzy_in_text(i, text) for i in gold["items"]) / len(gold["items"])
            if gold["items"]
            else 1.0
        ),
    }


def safe_div(a: float, b: float) -> float | None:
    return a / b if b else None


def guard_blocks_substitution(claim_text: str, amount: str, allowed_numbers: set[str],
                              allowed_dates: set) -> dict:
    """Substitute the amount in a claim and check the guard blocks it.

    Also checks the unmodified claim passes, so a guard that blocks everything
    does not count as a success.
    """
    from app.services.claim_guard import check_text

    n = normalize_number(amount)
    fake = f"{float(n) + 1000:.2f}" if n else "1000.00"
    fake_text = claim_text.replace(amount, fake.replace(".00", "").replace(".", ","))
    clean_ok = not check_text(claim_text, allowed_numbers, allowed_dates)
    blocked = bool(check_text(fake_text, allowed_numbers, allowed_dates))
    return {"clean_passes": clean_ok, "substituted_blocked": blocked}


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------
def _get_provider(mode: str):
    """Select the provider by mode without editing app code."""
    from app.core.config import settings
    from app.services.extract.service import get_provider

    settings.llm_mode = mode
    provider = get_provider()
    expected = {"rules": "RuleBasedProvider", "openai": "OpenAiProvider",
                "fixture": "FixtureProvider"}.get(mode)
    if expected and type(provider).__name__ != expected:
        # get_provider() may not know the mode yet: import the class directly.
        if mode == "rules":
            from app.services.extract.rules_provider import RuleBasedProvider
            return RuleBasedProvider()
        if mode == "openai":
            from app.services.extract.openai_provider import OpenAiProvider
            return OpenAiProvider()
    return provider


def _run_ocr(path: Path):
    from app.core.config import settings
    from app.services.ocr.tesseract_engine import TesseractEngine

    engine = TesseractEngine(langs=settings.ocr_langs, tesseract_cmd=settings.tesseract_cmd)
    return engine.recognize(path, "image/png")


def _grounding_and_hallucination(result, lines, ocr_text: str):
    """Return (grounded, total, hallucinated) over all extracted values."""
    from app.services.extract.grounding import is_grounded

    by_id = {l.line_no: l for l in lines}
    checks = []  # (field, kind, value, line_ids)
    f = result.fields
    for name, kind, fld in (("seller_name", "string", f.seller_name),
                            ("purchase_date", "date", f.purchase_date),
                            ("total_amount", "number", f.total_amount),
                            ("currency", "string", f.currency)):
        if fld is not None:
            checks.append((name, kind, fld.value, fld.line_ids))
    for it in f.items:
        checks.append(("item", "string", it.name, it.line_ids))
        if it.price:
            checks.append(("price", "number", it.price, it.line_ids))
    grounded = sum(is_grounded(n, v, ids, by_id) for n, _, v, ids in checks)
    halluc = 0
    for _, kind, v, _ in checks:
        present = fuzzy_in_text(v, ocr_text) if kind == "string" else value_in_text(kind, v, ocr_text)
        halluc += 0 if present else 1
    return grounded, len(checks), halluc


def evaluate_case(case_id: str, gold: dict, provider, ocr_only: bool) -> dict:
    from app.models import OcrLine
    from app.services.chat import detect_events, parse_whatsapp

    case_dir = CASES_DIR / case_id
    t0 = time.perf_counter()
    data_lines = _run_ocr(case_dir / "receipt.png")
    t_ocr = time.perf_counter() - t0
    ocr_text = "\n".join(d.text for d in data_lines)
    rec = {"case": case_id, "kind": gold.get("kind", ""), "ocr_seconds": round(t_ocr, 2),
           "ocr_recall": ocr_recall(gold, ocr_text), "ocr_text": ocr_text}

    # Chat event dates: parsed by code from chat.txt (no OCR involved).
    msgs = parse_whatsapp((case_dir / "chat.txt").read_text(encoding="utf-8"))
    events = {e.kind.value: e.date.isoformat() for e in detect_events(msgs, gold["seller"]) if e.date}
    rec["events_ok"] = events == gold.get("events", {})

    if ocr_only:
        return rec

    lines = [OcrLine(document_id=0, line_no=d.line_no, text=d.text, bbox_x=d.bbox_x,
                     bbox_y=d.bbox_y, bbox_w=d.bbox_w, bbox_h=d.bbox_h, page=d.page)
             for d in data_lines]
    import hashlib
    sha = hashlib.sha256((case_dir / "receipt.png").read_bytes()).hexdigest()
    t1 = time.perf_counter()
    try:
        result = provider.extract(sha, lines)
    except Exception as exc:  # report, never crash the whole run
        rec["error"] = f"{type(exc).__name__}: {exc}"[:200]
        return rec
    t_ext = time.perf_counter() - t1
    f = result.fields
    got = {
        "seller": f.seller_name.value if f.seller_name else None,
        "date": f.purchase_date.value if f.purchase_date else None,
        "total": f.total_amount.value if f.total_amount else None,
        "currency": f.currency.value if f.currency else None,
        "items": [i.name for i in f.items],
    }
    acc = {
        "seller": match_seller(got["seller"], gold["seller"]),
        "date": match_date(got["date"], gold["purchase_date"]),
        "total": match_total(got["total"], gold["total_amount"]),
        "currency": match_currency(got["currency"], gold["currency"]),
        "item": match_items(got["items"], gold["items"]),
    }
    g, n, h = _grounding_and_hallucination(result, lines, ocr_text)

    # Claim guard: build a claim from extracted values and substitute the amount.
    guard = None
    if got["total"] and normalize_number(got["total"]):
        amount = got["total"]
        allowed_n = {normalize_number(amount)}
        d = normalize_date(got["date"] or "")
        allowed_d = {d} if d else set()
        # Same formats as app/services/claim.py: dd.mm.yyyy date, plain amount.
        date_str = d.strftime("%d.%m.%Y") if d else ""
        text = f"Стоимость товара составила {amount} KZT. Дата покупки: {date_str}."
        guard = guard_blocks_substitution(text, amount, allowed_n, allowed_d)

    rec.update({"got": got, "accuracy": acc, "grounded": g, "facts": n, "hallucinated": h,
                "extract_seconds": round(t_ext, 3),
                "claim_seconds": round(t_ocr + t_ext, 2), "guard": guard})
    return rec


def _pct(x: float | None) -> str:
    return "  n/a" if x is None else f"{x * 100:4.0f}%"


def summarize(records: list[dict], ocr_only: bool) -> dict:
    n = len(records)
    s: dict = {"cases": n}
    s["ocr_recall"] = {k: safe_div(sum(float(r["ocr_recall"][k]) for r in records), n) for k in FIELDS}
    s["events_ok"] = safe_div(sum(r["events_ok"] for r in records), n)
    s["ocr_seconds_avg"] = round(sum(r["ocr_seconds"] for r in records) / n, 2) if n else None
    if ocr_only:
        return s
    ok = [r for r in records if "accuracy" in r]
    s["errors"] = n - len(ok)
    s["accuracy"] = {k: safe_div(sum(float(r["accuracy"][k]) for r in ok), len(ok)) for k in FIELDS}
    facts = sum(r["facts"] for r in ok)
    s["grounding"] = safe_div(sum(r["grounded"] for r in ok), facts)
    s["hallucination_rate"] = safe_div(sum(r["hallucinated"] for r in ok), facts)
    guards = [r["guard"] for r in ok if r["guard"]]
    s["guard_blocked"] = f"{sum(g['substituted_blocked'] and g['clean_passes'] for g in guards)}/{len(guards)}"
    s["claim_seconds_avg"] = round(sum(r["claim_seconds"] for r in ok) / len(ok), 2) if ok else None
    return s


def print_table(records: list[dict], summary: dict, ocr_only: bool) -> None:
    print("\nOCR-level recall (gold value found anywhere in Tesseract text):")
    print(f"{'case':10} {'kind':11} " + " ".join(f"{k:>8}" for k in FIELDS) + "   ocr_s")
    for r in records:
        print(f"{r['case']:10} {r['kind']:11} " + " ".join(f"{_pct(r['ocr_recall'][k]):>8}" for k in FIELDS)
              + f"   {r['ocr_seconds']:.2f}")
    print(f"{'AVG':10} {'':11} " + " ".join(f"{_pct(summary['ocr_recall'][k]):>8}" for k in FIELDS))
    print(f"chat event dates correct: {_pct(summary['events_ok'])}")
    if ocr_only:
        return
    print("\nExtraction accuracy (value equals gold):")
    print(f"{'case':10} {'kind':11} " + " ".join(f"{k:>8}" for k in FIELDS) + "  ground halluc guard  claim_s")
    for r in records:
        if "accuracy" not in r:
            print(f"{r['case']:10} {r['kind']:11} ERROR {r.get('error','')}")
            continue
        gd = r["guard"]
        gs = "n/a" if not gd else ("block" if gd["substituted_blocked"] and gd["clean_passes"] else "FAIL")
        print(f"{r['case']:10} {r['kind']:11} " + " ".join(f"{_pct(r['accuracy'][k]):>8}" for k in FIELDS)
              + f"  {r['grounded']}/{r['facts']:<3} {r['hallucinated']:>5} {gs:>6}  {r['claim_seconds']:.2f}")
    a = summary.get("accuracy", {})
    print(f"{'AVG':10} {'':11} " + " ".join(f"{_pct(a.get(k)):>8}" for k in FIELDS))
    print(f"grounding {_pct(summary['grounding'])} | hallucination {_pct(summary['hallucination_rate'])} "
          f"| guard blocks substituted amount {summary['guard_blocked']} "
          f"| avg time to claim {summary['claim_seconds_avg']}s | errors {summary['errors']}")


def print_comparison(summary: dict, prev: dict, prev_name: str) -> None:
    print(f"\nComparison with previous run ({prev_name}):")
    for section in ("ocr_recall", "accuracy"):
        if section in summary and section in prev.get("summary", {}):
            for k in FIELDS:
                a, b = summary[section].get(k), prev["summary"][section].get(k)
                if a is not None and b is not None:
                    print(f"  {section}.{k}: {b*100:.0f}% -> {a*100:.0f}% ({(a-b)*100:+.0f})")
    for k in ("grounding", "hallucination_rate"):
        a, b = summary.get(k), prev["summary"].get(k)
        if a is not None and b is not None:
            print(f"  {k}: {b*100:.0f}% -> {a*100:.0f}%")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--mode", default="rules", choices=["rules", "openai", "auto", "fixture"])
    ap.add_argument("--cases", nargs="*", help="case ids (default: all in gold.json)")
    ap.add_argument("--ocr-only", action="store_true", help="skip extraction, OCR metrics only")
    ap.add_argument("--no-save", action="store_true", help="do not write results snapshot")
    args = ap.parse_args()

    os.environ["OCR_ENGINE"] = "tesseract"
    from app.core.config import settings
    settings.ocr_engine = "tesseract"

    gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    ids = args.cases or sorted(gold)
    provider = None
    ocr_only = args.ocr_only
    if not ocr_only:
        try:
            provider = _get_provider(args.mode)
        except Exception as exc:
            print(f"[warn] provider for mode={args.mode} unavailable ({exc}); OCR-level metrics only")
            ocr_only = True

    records = [evaluate_case(c, gold[c], provider, ocr_only) for c in ids]
    summary = summarize(records, ocr_only)
    print(f"mode={'ocr-only' if ocr_only else args.mode} ocr_langs={settings.ocr_langs} cases={len(ids)}")
    print_table(records, summary, ocr_only)

    mode_name = "ocr-only" if ocr_only else args.mode
    prev_files = sorted(RESULTS_DIR.glob(f"{mode_name}-*.json"))
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    out = {"mode": mode_name, "timestamp": stamp, "ocr_langs": settings.ocr_langs,
           "label": os.environ.get("EVAL_LABEL", ""), "summary": summary, "cases": records}
    if prev_files:
        prev = json.loads(prev_files[-1].read_text(encoding="utf-8"))
        print_comparison(summary, prev, prev_files[-1].name)
    LAST_RUN.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    if not args.no_save:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        (RESULTS_DIR / f"{mode_name}-{stamp}.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
