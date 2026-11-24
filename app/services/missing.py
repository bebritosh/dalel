"""Missing-evidence engine M1-M5. Computed live from the case state.

Returns every rule with a resolved flag so the UI can show open items and
strike through the closed ones.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from sqlmodel import Session, select

from app.models import Document, DocumentKind, Event, EventKind, Fact
from app.schemas.missing import MissingItemRead

_RULES_PATH = Path("rules/missing_evidence.yaml")

_KEY_FIELDS = ("seller_name", "purchase_date", "total_amount")


def _load_rules() -> list[dict]:
    data = yaml.safe_load(_RULES_PATH.read_text(encoding="utf-8"))
    return list(data.get("rules", []))


def get_missing(session: Session, case_id: int) -> list[MissingItemRead]:
    """Evaluate all missing-evidence rules for a case."""
    docs = session.exec(select(Document).where(Document.case_id == case_id)).all()
    facts = session.exec(select(Fact).where(Fact.case_id == case_id)).all()
    events = session.exec(select(Event).where(Event.case_id == case_id)).all()

    kinds = {d.kind for d in docs}
    by_field = {f.field: f for f in facts}
    event_kinds = {e.kind for e in events}

    def no_warranty() -> bool:
        warranty_fact = by_field.get("warranty_period")
        has_fact = bool(warranty_fact and warranty_fact.value)
        return not (DocumentKind.warranty in kinds or has_fact)

    def no_contact_date() -> bool:
        return not any(
            e.kind == EventKind.contact and e.date for e in events
        )

    def no_defect_media() -> bool:
        return DocumentKind.photo not in kinds

    def no_written_refusal() -> bool:
        return EventKind.refusal not in event_kinds

    def receipt_unreadable() -> bool:
        if DocumentKind.receipt not in kinds:
            return True
        for field in _KEY_FIELDS:
            f = by_field.get(field)
            if f is None or not f.grounded:
                return True
        return False

    checks = {
        "no_warranty": no_warranty,
        "no_contact_date": no_contact_date,
        "no_defect_media": no_defect_media,
        "no_written_refusal": no_written_refusal,
        "receipt_unreadable": receipt_unreadable,
    }

    results: list[MissingItemRead] = []
    for rule in _load_rules():
        is_missing = checks[rule["check"]]()
        results.append(
            MissingItemRead(
                rule_id=rule["id"],
                title=rule["title"],
                why=rule["why"],
                fix=rule["fix"],
                resolved=not is_missing,
            )
        )
    return results
