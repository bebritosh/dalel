"""Chat export parsing (WhatsApp txt) and heuristic event detection.

Supports both WhatsApp export formats:
    Android:  06.11.2026, 10:15 - Author Name: message text
    iOS:      [06.11.2026, 10:15:32] Author Name: message text
Multi-line messages are joined; WhatsApp system notices (encryption banner,
media placeholders, deleted messages, group changes) are skipped.

All detected events are marked needs_review: the heuristics are deliberately
simple and the user confirms them.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date

from app.models import EventKind
from app.services.extract.normalize import normalize_date

# Android: "06.11.2026, 10:15 - Author Name: message text" (time may carry seconds / AM-PM).
_ANDROID_RE = re.compile(
    r"^(?P<date>\d{1,2}[./]\d{1,2}[./]\d{2,4}),?\s+"
    r"(?P<time>\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\s*-\s*"
    r"(?P<author>[^:]+?):\s?(?P<text>.*)$"
)

# iOS: "[06.11.2026, 10:15:32] Author Name: message text".
_IOS_RE = re.compile(
    r"^\[(?P<date>\d{1,2}[./]\d{1,2}[./]\d{2,4}),?\s+"
    r"(?P<time>\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\]\s*"
    r"(?P<author>[^:]+?):\s?(?P<text>.*)$"
)

# A timestamped line that is NOT a normal "author: text" message is a system
# notice (e.g. the encryption banner). Used to skip it instead of appending it
# as a continuation of the previous message.
_TS_PREFIX_RE = re.compile(r"^\[?\d{1,2}[./]\d{1,2}[./]\d{2,4},?\s+\d{1,2}:\d{2}")

# Bidirectional marks WhatsApp/iOS insert around timestamps and media tags.
_BIDI_MARKS = dict.fromkeys(
    map(ord, "‎‏‪‫‬⁦⁧⁨⁩"), None
)

# Lowercased substrings that mark a system notice or content-free placeholder.
_SYSTEM_SUBSTRINGS = (
    "end-to-end encrypted",
    "end‑to‑end encrypted",
    "messages and calls are",
    "сквозным шифрованием",
    "зашифрованы",
    "security code changed",
    "код безопасности",
    "this message was deleted",
    "you deleted this message",
    "сообщение удалено",
    "сообщение было удалено",
    "вы удалили это сообщение",
    "media omitted",
    "媒体",
    "медиафайл пропущен",
    "медиафайл отсутствует",
    "изображение отсутствует",
    "<attached",
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
    message_id: str = ""  # "line:N" — source line where the message starts


@dataclass
class DetectedEvent:
    """A timeline event detected from chat, not yet persisted."""

    date: date | None
    kind: EventKind
    description: str


def _is_system(text: str) -> bool:
    low = text.casefold().strip()
    if low in ("<media omitted>", "<медиафайл пропущен>"):
        return True
    return any(s in low for s in _SYSTEM_SUBSTRINGS)


def parse_whatsapp(content: str) -> list[ChatMessage]:
    """Parse a WhatsApp txt export (Android or iOS) into messages.

    Multi-line messages are joined. System notices and media placeholders are
    skipped and never attached to a neighbouring message.
    """
    messages: list[ChatMessage] = []
    allow_continuation = False  # only a real message can receive continuations
    for line_no, raw in enumerate(content.splitlines()):
        line = raw.translate(_BIDI_MARKS).strip()
        if not line:
            continue
        m = _ANDROID_RE.match(line) or _IOS_RE.match(line)
        if m:
            text = m.group("text").strip()
            if _is_system(text) or _is_system(m.group("author")):
                allow_continuation = False
                continue
            messages.append(
                ChatMessage(
                    date=normalize_date(m.group("date")),
                    time=m.group("time").strip(),
                    author=m.group("author").strip(),
                    text=text,
                    message_id=f"line:{line_no}",
                )
            )
            allow_continuation = True
        elif _TS_PREFIX_RE.match(line):
            # Timestamped but not "author: text" → a system notice; skip it.
            allow_continuation = False
        elif allow_continuation and messages:
            messages[-1].text += " " + line
    return messages


def _telegram_text(value) -> str:
    """Flatten Telegram's text field (a string or a list of fragments)."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text", "")))
        return "".join(parts)
    return ""


def parse_telegram(content: str) -> list[ChatMessage]:
    """Parse a Telegram Desktop export (result.json) into messages.

    Only real messages (type == "message") are kept; service messages are
    skipped. message_id is Telegram's own numeric id as a string.
    """
    try:
        data = json.loads(content)
    except (ValueError, TypeError):
        return []
    raw_messages = data.get("messages", []) if isinstance(data, dict) else []
    messages: list[ChatMessage] = []
    for item in raw_messages:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        text = _telegram_text(item.get("text", "")).strip()
        author = str(item.get("from") or "").strip()
        iso = str(item.get("date") or "")
        day = normalize_date(iso.split("T")[0]) if iso else None
        time = iso.split("T")[1][:8] if "T" in iso else ""
        messages.append(
            ChatMessage(
                date=day,
                time=time,
                author=author,
                text=text,
                message_id=str(item.get("id", "")),
            )
        )
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
