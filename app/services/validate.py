"""Validation engine V1-V4. Pure computation over current facts and events."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml
from sqlmodel import Session, select

from app.models import Event, EventKind, Fact
from app.schemas.checks import CheckResult
from app.services.extract.normalize import normalize_date, normalize_number
from app.services.photo_checks import check_photos

_RULES_PATH = Path("rules/validation.yaml")

_KEY_FIELDS = ("seller_name", "purchase_date", "total_amount")


def _load_rules() -> dict[str, dict]:
    data = yaml.safe_load(_RULES_PATH.read_text(encoding="utf-8"))
    return {rule["id"]: rule for rule in data.get("rules", [])}


def run_checks(session: Session, case_id: int) -> list[CheckResult]:
    """Run checks V1-V4 and return findings."""
    rules = _load_rules()
    facts = session.exec(select(Fact).where(Fact.case_id == case_id)).all()
    events = session.exec(select(Event).where(Event.case_id == case_id)).all()
    by_field = {f.field: f for f in facts}
    results: list[CheckResult] = []

    def mk(code: str, fact_ids=None, event_ids=None, extra: str = "") -> CheckResult:
        rule = rules[code]
        return CheckResult(
            code=code,
            severity=rule["severity"],
            message=rule["message"] + (f" {extra}" if extra else ""),
            fact_ids=fact_ids or [],
            event_ids=event_ids or [],
        )

    # V1: value grounded in the source document.
    for f in facts:
        is_key = f.field in _KEY_FIELDS or f.field.startswith("item_")
        if is_key and f.value and not f.grounded:
            results.append(mk("V1", fact_ids=[f.id], extra=f"Поле: {f.field}."))

    # V2: purchase date valid and not in the future.
    pdate_fact = by_field.get("purchase_date")
    if pdate_fact and pdate_fact.value:
        parsed = normalize_date(pdate_fact.value)
        if parsed is None or parsed > date.today():
            results.append(mk("V2", fact_ids=[pdate_fact.id]))

    # V3: total equals the sum of item prices.
    total_fact = by_field.get("total_amount")
    price_facts = [f for f in facts if f.field.endswith("_price")]
    if total_fact and total_fact.value and price_facts:
        total = normalize_number(total_fact.value)
        parts = [normalize_number(f.value) for f in price_facts]
        if total is not None and all(p is not None for p in parts):
            items_sum = sum(float(p) for p in parts)
            if abs(items_sum - float(total)) > 0.01:
                results.append(
                    mk(
                        "V3",
                        fact_ids=[total_fact.id] + [f.id for f in price_facts],
                        extra=f"Позиции: {items_sum:.2f}, чек: {float(total):.2f}.",
                    )
                )

    # V4: purchase -> contact -> refusal date order.
    def event_date(kind: EventKind) -> tuple[date | None, int | None]:
        for e in events:
            if e.kind == kind and e.date:
                return e.date, e.id
        return None, None

    pur_d, pur_id = event_date(EventKind.purchase)
    con_d, con_id = event_date(EventKind.contact)
    ref_d, ref_id = event_date(EventKind.refusal)
    if pur_d and con_d and pur_d > con_d:
        results.append(mk("V4", event_ids=[i for i in (pur_id, con_id) if i]))
    if con_d and ref_d and con_d > ref_d:
        results.append(mk("V4", event_ids=[i for i in (con_id, ref_id) if i]))

    # Photo-quality checks (P1-P4) over defect photos (warnings, never block).
    results.extend(check_photos(session, case_id))

    return results
