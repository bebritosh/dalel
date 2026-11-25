"""Claim assembly from confirmed facts and events only.

The text is built strictly from confirmed facts (and event dates). No free LLM
text is used. Legal references come only from rules/legal_refs.json as stubs.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from sqlmodel import Session, select

from app.models import Case, CaseStatus, Claim, Event, EventKind, Fact
from app.services.claim_guard import GuardError, check_text
from app.services.extract.normalize import (
    iter_dates,
    iter_numbers,
    normalize_date,
)

_LEGAL_PATH = Path("rules/legal_refs.json")
_REQUIRED = ("seller_name", "purchase_date", "total_amount")

# Characters not allowed in XML 1.0. OCR can emit control characters (U+0000..
# U+001F except tab/newline/CR); if they reach the DOCX, Word refuses to open it
# ("content cannot be read"). Strip them once, before any substitution.
_XML_INVALID = re.compile(
    "[^\u0009\u000a\u000d -퟿-�\U00010000-\U0010ffff]"
)


def _xml_safe(value: str) -> str:
    """Remove characters invalid in XML 1.0 (keeps tab/newline/CR)."""
    return _XML_INVALID.sub("", value or "")


class RequiredFieldsError(Exception):
    """Raised when required fields are not confirmed yet."""

    def __init__(self, missing: list[str]) -> None:
        self.missing = missing
        super().__init__("Required fields not confirmed: " + ", ".join(missing))


@dataclass
class ClaimBuild:
    """Result of assembling a claim: the rendered text and its grounding."""

    text: str
    context: dict
    fact_ids: list[int] = field(default_factory=list)
    allowed_numbers: set[str] = field(default_factory=set)
    allowed_dates: set = field(default_factory=set)


def _fmt_date(d: date | None) -> str:
    return d.strftime("%d.%m.%Y") if d else ""


def _fmt_amount(value: str) -> str:
    """Format '249990.00' as '249 990,00' (space thousands, comma decimals)."""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return value
    whole, frac = f"{num:.2f}".split(".")
    sign = "-" if whole.startswith("-") else ""
    whole = whole.lstrip("-")
    grouped = f"{int(whole):,}".replace(",", " ")
    return f"{sign}{grouped},{frac}"


def _load_legal() -> list[dict]:
    data = json.loads(_LEGAL_PATH.read_text(encoding="utf-8"))
    return data.get("refs", [])


def build_claim(session: Session, case: Case) -> ClaimBuild:
    """Assemble the claim text and its allowed-value sets. May raise errors."""
    facts = session.exec(select(Fact).where(Fact.case_id == case.id)).all()
    events = session.exec(select(Event).where(Event.case_id == case.id)).all()

    confirmed = {f.field: f for f in facts if f.confirmed_by_user}
    missing = [name for name in _REQUIRED if name not in confirmed]
    if missing:
        raise RequiredFieldsError(missing)

    # Allowed values from confirmed facts and event dates.
    allowed_numbers: set[str] = set()
    allowed_dates: set[date] = set()
    used_fact_ids: list[int] = []
    for f in confirmed.values():
        allowed_numbers.update(iter_numbers(f.value))
        allowed_dates.update(iter_dates(f.value))
        used_fact_ids.append(f.id)
    for e in events:
        if e.date:
            allowed_dates.add(e.date)

    # Sanitize every user/OCR-derived string once, here, before it enters the
    # claim text or the DOCX context. Numbers/dates are reformatted from
    # normalized values and need no cleaning.
    seller = _xml_safe(confirmed["seller_name"].value)
    purchase_date = normalize_date(confirmed["purchase_date"].value)
    amount = _fmt_amount(confirmed["total_amount"].value)
    currency = _xml_safe(confirmed["currency"].value) if "currency" in confirmed else ""

    items = [
        _xml_safe(confirmed[k].value)
        for k in sorted(confirmed)
        if k.startswith("item_") and not k.endswith("_price")
    ]
    item_desc = "; ".join(items) if items else "товар"

    def event_date(kind: EventKind) -> date | None:
        for e in events:
            if e.kind == kind and e.date:
                return e.date
        return None

    contact_d = event_date(EventKind.contact)
    refusal_d = event_date(EventKind.refusal)

    legal = _load_legal()

    context = {
        "seller": seller,
        "item_desc": item_desc,
        "purchase_date": _fmt_date(purchase_date),
        "amount": amount,
        "currency": currency,
        "contact_date": _fmt_date(contact_d),
        "refusal_date": _fmt_date(refusal_d),
        "legal": legal,
    }

    # Build the authoritative plain text (guard runs on this; DOCX mirrors it).
    lines: list[str] = []
    lines.append("ПРЕТЕНЗИЯ")
    lines.append("")
    lines.append(f"Кому: {seller}")
    lines.append("От кого: [ФИО заявителя], [адрес заявителя], [контактные данные]")
    lines.append("")
    amount_str = f"{amount} {currency}".strip()
    lines.append(
        f"Я приобрёл(а) у продавца {seller} товар: {item_desc}. "
        f"Дата покупки: {context['purchase_date']}. "
        f"Стоимость товара составила {amount_str}."
    )
    lines.append(
        "В процессе эксплуатации в товаре обнаружился недостаток, "
        "товар оказался ненадлежащего качества."
    )
    lines.append("")
    lines.append("Хронология обращения:")
    lines.append(f"— {context['purchase_date']}: покупка товара.")
    if contact_d:
        lines.append(f"— {context['contact_date']}: обращение к продавцу.")
    if refusal_d:
        lines.append(
            f"— {context['refusal_date']}: продавец отказал в удовлетворении требования."
        )
    lines.append("")
    lines.append("Требование:")
    lines.append(
        f"Прошу вернуть уплаченную за товар денежную сумму {amount_str}."
    )
    lines.append("")
    lines.append("Приложения:")
    lines.append("— копия чека;")
    lines.append("— экспорт переписки с продавцом.")
    lines.append("")
    lines.append("Правовое обоснование:")
    for ref in legal:
        lines.append(f"— {ref['title']}: [норма уточняется юристом].")
    lines.append("")
    lines.append("[ФИО заявителя], подпись, дата.")

    text = "\n".join(lines)

    return ClaimBuild(
        text=text,
        context=context,
        fact_ids=used_fact_ids,
        allowed_numbers=allowed_numbers,
        allowed_dates=allowed_dates,
    )


def create_claim(session: Session, case: Case) -> Claim:
    """Build, guard, persist and return a claim. Raises GuardError on violations."""
    build = build_claim(session, case)

    violations = check_text(build.text, build.allowed_numbers, build.allowed_dates)
    if violations:
        raise GuardError(violations)

    last = session.exec(
        select(Claim).where(Claim.case_id == case.id).order_by(Claim.version.desc())
    ).first()
    version = (last.version + 1) if last else 1
    claim = Claim(
        case_id=case.id,
        version=version,
        text=build.text,
        fact_ids=build.fact_ids,
    )
    session.add(claim)
    case.status = CaseStatus.claim_ready
    session.add(case)
    session.commit()
    session.refresh(claim)
    return claim
