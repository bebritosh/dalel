"""Timeline: build events from facts + chat, and return them ordered."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from sqlmodel import Session, select

from app.models import Document, DocumentKind, Event, EventKind, Fact
from app.services.chat import detect_events, parse_telegram, parse_whatsapp
from app.services.extract.normalize import normalize_date


def _fact(session: Session, case_id: int, field: str) -> Fact | None:
    return session.exec(
        select(Fact).where(Fact.case_id == case_id, Fact.field == field)
    ).first()


def build_events(session: Session, case_id: int) -> list[Event]:
    """Create timeline events for a case (idempotent: skips if any exist)."""
    existing = session.exec(select(Event).where(Event.case_id == case_id)).all()
    if existing:
        return list(existing)

    seller_fact = _fact(session, case_id, "seller_name")
    seller_name = seller_fact.value if seller_fact else ""

    created: list[Event] = []

    # Purchase event from the purchase_date fact.
    pdate_fact = _fact(session, case_id, "purchase_date")
    if pdate_fact and pdate_fact.value:
        pdate = normalize_date(pdate_fact.value)
        receipt = session.exec(
            select(Document).where(
                Document.case_id == case_id, Document.kind == DocumentKind.receipt
            )
        ).first()
        created.append(
            Event(
                case_id=case_id,
                date=pdate,
                kind=EventKind.purchase,
                description="Покупка товара по чеку",
                document_id=receipt.id if receipt else None,
                needs_review=True,
            )
        )

    # Events detected from chat exports (WhatsApp txt).
    chat_docs = session.exec(
        select(Document).where(
            Document.case_id == case_id, Document.kind == DocumentKind.chat
        )
    ).all()
    for doc in chat_docs:
        path = Path(doc.stored_path)
        suffix = path.suffix.lower()
        if not path.exists() or suffix not in (".txt", ".json"):
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        messages = parse_telegram(content) if suffix == ".json" else parse_whatsapp(content)
        for det in detect_events(messages, seller_name):
            created.append(
                Event(
                    case_id=case_id,
                    date=det.date,
                    kind=det.kind,
                    description=det.description,
                    document_id=doc.id,
                    message_id=det.message_id,
                    needs_review=True,
                )
            )

    for event in created:
        session.add(event)
    session.commit()
    for event in created:
        session.refresh(event)
    return created


_ORDER = {
    EventKind.purchase: 0,
    EventKind.defect: 1,
    EventKind.contact: 2,
    EventKind.reply: 3,
    EventKind.refusal: 4,
    EventKind.other: 5,
}


def get_timeline(session: Session, case_id: int) -> list[Event]:
    """Return events ordered by date, then by a sensible kind order."""
    events = session.exec(select(Event).where(Event.case_id == case_id)).all()
    return sorted(
        events,
        key=lambda e: (e.date or date.max, _ORDER.get(e.kind, 9)),
    )
