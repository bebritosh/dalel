"""WhatsApp parser: Android + iOS formats, multi-line, system lines."""

from __future__ import annotations

from datetime import date

from app.services.chat import detect_events, parse_whatsapp

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
