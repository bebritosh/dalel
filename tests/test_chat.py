"""WhatsApp parser: Android + iOS formats, multi-line, system lines."""

from __future__ import annotations

from datetime import date

import json

from app.services.chat import detect_events, parse_telegram, parse_whatsapp

ANDROID = """06.11.2026, 10:15 - Арман: Здравствуйте! Купил смартфон, экран мигает.
Отправляю детали позже.
06.11.2026, 11:40 - Пример Электроникс: Пришлите фото дефекта.
09.11.2026, 16:20 - Пример Электроникс: Вернуть деньги не можем, случай не гарантийный.
"""

IOS = """[06.11.2026, 10:15:03] Арман: Здравствуйте! Купил смартфон, экран мигает.
[06.11.2026, 11:40:12] Пример Электроникс: Пришлите фото дефекта.
[09.11.2026, 16:20:47] Пример Электроникс: Вернуть деньги не можем, случай не гарантийный.
"""


def test_android_format_parses_messages():
    msgs = parse_whatsapp(ANDROID)
    assert len(msgs) == 3
    assert msgs[0].date == date(2026, 11, 6)
    assert msgs[0].author == "Арман"
    # Continuation line joined into the first message.
    assert "Отправляю детали позже." in msgs[0].text


def test_ios_format_parses_messages():
    msgs = parse_whatsapp(IOS)
    assert len(msgs) == 3
    assert msgs[0].date == date(2026, 11, 6)
    assert msgs[0].author == "Арман"
    assert msgs[0].time == "10:15:03"


def test_message_id_points_at_source_line():
    msgs = parse_whatsapp(ANDROID)
    assert msgs[0].message_id == "line:0"
    # Second message starts after the first message + its continuation line.
    assert msgs[1].message_id == "line:2"


def test_system_lines_are_skipped():
    content = (
        "06.11.2026, 10:00 - Messages and calls are end-to-end encrypted. "
        "Tap to learn more.\n"
        "06.11.2026, 10:15 - Арман: Здравствуйте!\n"
        "06.11.2026, 10:16 - Арман: <Media omitted>\n"
        "06.11.2026, 10:20 - Пример Электроникс: Это сообщение было удалено\n"
    )
    msgs = parse_whatsapp(content)
    texts = [m.text for m in msgs]
    assert texts == ["Здравствуйте!"]  # only the one real text message survives


def test_encryption_notice_does_not_attach_as_continuation():
    content = (
        "06.11.2026, 10:15 - Арман: Первое сообщение.\n"
        "06.11.2026, 10:16 - Messages and calls are end-to-end encrypted.\n"
        "обычная строка продолжения отброшена, т.к. предыдущая — системная\n"
    )
    msgs = parse_whatsapp(content)
    assert len(msgs) == 1
    assert msgs[0].text == "Первое сообщение."


def test_detect_events_still_works_on_both_formats():
    for content in (ANDROID, IOS):
        events = {e.kind.value: e.date for e in detect_events(parse_whatsapp(content), "Пример Электроникс")}
        assert events["contact"] == date(2026, 11, 6)
        assert events["refusal"] == date(2026, 11, 9)


TELEGRAM = json.dumps({
    "name": "Пример Электроникс",
    "type": "personal_chat",
    "messages": [
        {"id": 100, "type": "service", "date": "2026-11-06T09:00:00", "action": "create_group"},
        {"id": 101, "type": "message", "date": "2026-11-06T10:15:03", "from": "Арман",
         "from_id": "user1", "text": "Здравствуйте! Купил смартфон, экран мигает."},
        {"id": 102, "type": "message", "date": "2026-11-08T09:05:00", "from": "Арман",
         "from_id": "user1", "text": ["Смотрите ", {"type": "link", "text": "http://ex.kz/photo"}, " — вот дефект."]},
        {"id": 103, "type": "message", "date": "2026-11-09T16:20:47", "from": "Пример Электроникс",
         "from_id": "user2", "text": "Вернуть деньги не можем, случай не гарантийный."},
    ],
}, ensure_ascii=False)


def test_telegram_parses_plain_message():
    msgs = parse_telegram(TELEGRAM)
    assert len(msgs) == 3  # service message skipped
    assert msgs[0].message_id == "101"
    assert msgs[0].date == date(2026, 11, 6)
    assert msgs[0].time == "10:15:03"
    assert msgs[0].author == "Арман"


def test_telegram_flattens_fragment_text_with_link():
    msgs = parse_telegram(TELEGRAM)
    assert msgs[1].text == "Смотрите http://ex.kz/photo — вот дефект."


def test_telegram_service_messages_skipped():
    msgs = parse_telegram(TELEGRAM)
    assert all(m.message_id != "100" for m in msgs)


def test_telegram_detect_events():
    events = {e.kind.value: e.date for e in detect_events(parse_telegram(TELEGRAM), "Пример Электроникс")}
    assert events["contact"] == date(2026, 11, 6)
    assert events["refusal"] == date(2026, 11, 9)


def test_telegram_invalid_json_returns_empty():
    assert parse_telegram("{not json") == []


def test_events_carry_message_id():
    events = detect_events(parse_whatsapp(ANDROID), "Пример Электроникс")
    assert all(e.message_id for e in events)
    by_kind = {e.kind.value: e for e in events}
    assert by_kind["contact"].message_id == "line:0"


def test_reply_detected_before_refusal():
    kinds = [e.kind.value for e in detect_events(parse_whatsapp(ANDROID), "Пример Электроникс")]
    # seller first acknowledges ("Пришлите фото") then refuses later.
    assert kinds == ["contact", "reply", "refusal"]


def test_no_reply_when_seller_refuses_immediately():
    content = (
        "06.11.2026, 10:15 - Арман: Купил смартфон, экран мигает.\n"
        "06.11.2026, 11:00 - Пример Электроникс: Вернуть деньги не можем, не гарантийный случай.\n"
    )
    kinds = [e.kind.value for e in detect_events(parse_whatsapp(content), "Пример Электроникс")]
    assert kinds == ["contact", "refusal"]


def test_no_event_without_source_message_id():
    from app.services.chat import ChatMessage

    msgs = [
        ChatMessage(date=date(2026, 11, 6), time="10:15", author="Арман", text="Привет", message_id=""),
    ]
    assert detect_events(msgs, "Пример Электроникс") == []
