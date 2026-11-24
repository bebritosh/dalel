"""Chat export parsing (WhatsApp txt) and heuristic event detection.

Telegram JSON is intentionally out of scope for this MVP build (see PLAN.md).
All detected events are marked needs_review: the heuristics are deliberately
simple and the user confirms them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from app.models import EventKind
from app.services.extract.normalize import normalize_date

# "06.11.2026, 10:15 - Author Name: message text"
_MSG_RE = re.compile(
    r"^(?P<date>\d{1,2}[./]\d{1,2}[./]\d{2,4}),?\s+"
    r"(?P<time>\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*"
    r"(?P<author>[^:]+?):\s?(?P<text>.*)$"
)

_REFUSAL_KEYWORDS = (
    "не можем",
    "отказ",
    "отказыва",
    "не подлежит",
    "не гарантийн",
    "не возврат",
    "возврат невозмож",
)


@dataclass
class ChatMessage:
    """One parsed chat message."""

    date: date | None
    time: str
    author: str
    text: str


@dataclass
class DetectedEvent:
    """A timeline event detected from chat, not yet persisted."""

    date: date | None
    kind: EventKind
    description: str


def parse_whatsapp(content: str) -> list[ChatMessage]:
    """Parse a WhatsApp txt export into messages (multi-line aware)."""
    messages: list[ChatMessage] = []
    for raw in content.splitlines():
        m = _MSG_RE.match(raw.strip())
        if m:
            messages.append(
                ChatMessage(
                    date=normalize_date(m.group("date")),
                    time=m.group("time"),
                    author=m.group("author").strip(),
                    text=m.group("text").strip(),
                )
            )
        elif messages and raw.strip():
            # Continuation of the previous message.
            messages[-1].text += " " + raw.strip()
    return messages


def _tokens(name: str) -> set[str]:
    return {t for t in re.split(r"[\s«».,\"]+", name.casefold()) if len(t) >= 4}


def _is_seller(author: str, seller_name: str) -> bool:
    if not seller_name:
        return False
    return bool(_tokens(author) & _tokens(seller_name))


def detect_events(
    messages: list[ChatMessage], seller_name: str = ""
) -> list[DetectedEvent]:
    """Detect first contact (buyer) and refusal (seller) events."""
    events: list[DetectedEvent] = []

    # First message from the buyer (a non-seller author) is the first contact.
    for msg in messages:
        if not _is_seller(msg.author, seller_name):
            events.append(
                DetectedEvent(
                    date=msg.date,
                    kind=EventKind.contact,
                    description=f"Первое обращение к продавцу: «{msg.text[:120]}»",
                )
            )
            break

    # First seller message containing refusal wording is the refusal.
    for msg in messages:
        if _is_seller(msg.author, seller_name):
            low = msg.text.casefold()
            if any(k in low for k in _REFUSAL_KEYWORDS):
                events.append(
                    DetectedEvent(
                        date=msg.date,
                        kind=EventKind.refusal,
                        description=f"Отказ продавца: «{msg.text[:120]}»",
                    )
                )
                break

    return events
