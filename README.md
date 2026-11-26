# DÄLEL

Конструктор доказательной претензии по некачественному товару (Казахстан): человек загружает чек и переписку, система извлекает поля с привязкой к строкам чека, строит хронологию, показывает недостающие доказательства и собирает претензию в DOCX/PDF, где каждое число и дата подтверждены фактом.

> Прототип для хакатона SDG Impact 2026. На демо — только синтетические данные.

## Статус на 26.11.2026
Проверено прогоном на этой машине (ветка `opus/2026-11-26`):
- **`pytest -q` → 92 passed, 0 skipped, 0 failed.**
- Фронтенд: `npm run typecheck` / `lint` / `build` / `build:mock` — зелёные.

**Работает:** загрузка файлов (jpg/png/pdf/txt/json/mp4, 15 МБ) → OCR (fixture/tesseract/auto) → извлечение полей с grounding (fixture/openai/live/rules, режим `auto`) → подтверждение полей → проверки V1–V4 и качества фото P1–P4 → хронология → список недостающего M1–M5 → претензия с guard (по исходному тексту и по готовому DOCX) → экспорт **DOCX и PDF**. Переписка: WhatsApp (Android и iOS) и Telegram (`result.json`), события по словарю `rules/chat_events.yaml` со ссылкой на сообщение. Нормы: 6 статей Закона РК из `rules/legal_refs.json` (`lawyer_reviewed=false`). Фронтенд: три экрана, языки **RU / EN / KK** (KK — черновой перевод, EN по умолчанию), mock- и http-режимы, адаптив 1440/390. Авто-миграция БД на старте (удалять `data/dalel.db` не нужно).

**На этой машине установлены** Tesseract (`rus+eng`) и LibreOffice — поэтому eval `--mode rules` прогоняется (grounding 100%, guard 9/9, events_ok 100%), а PDF-экспорт отдаёт настоящий файл.

**Не сделано / не проверено:** проверки V5–V8, распознавание дефекта на фото, PaddleOCR, dark mode; калибровка порогов фото на реальных снимках; ответ юриста по 6 нормам и по смартфону (п. 1-1 ст. 15); проверка DOCX в **настоящем Word на Windows** (подтверждены только парсинг XML и LibreOffice); живой провайдер Anthropic (нет ключа); eval-цифры openai (нет ключа); прогон на чистом Windows по HANDOFF; проверка казахского носителем; ZIP-архив дела, второе обращение, `.ics`, «сбросить демо», печатная версия. Подробнее — [docs/PLAN.md](docs/PLAN.md).

## Запуск (Windows)
Первая настройка один раз — см. [docs/HANDOFF.md](docs/HANDOFF.md). Затем в двух терминалах:
```
# 1) бэкенд, из корня репозитория
.venv\Scripts\python -m uvicorn app.main:app --reload
# 2) фронтенд, из frontend\
npm run dev
# 3) открыть в браузере
http://localhost:5173
```
Бэкенд — `http://127.0.0.1:8000` (Swagger `/docs`); фронтенд проксирует `/api` на 8000. Если порт 5173 занят, Vite выберет следующий (5174+) — смотри адрес в его выводе.

- **Tesseract** (языки `rus+eng`) нужен для живого OCR и eval. Если не в PATH — задать `TESSERACT_CMD` в `.env`.
- **LibreOffice** нужен **только для PDF**. Путь — `SOFFICE_PATH` (или стандартная установка; находится автоматически). Без него `?format=pdf` отдаёт 503, DOCX работает всегда.

Демо-файлы: `eval\cases\demo-001\` (`receipt.png` → «Чек», `chat.txt` → «Переписка»).
Режим без бэкенда (для жюри): в `frontend\` — `npm run dev:mock` (статическая сборка `npm run build:mock`, папка `dist-mock/`).

## Режимы извлечения и приватность
`LLM_MODE = fixture | rules | openai | live | auto` (см. `.env.example`). `rules` — **rule-based baseline** (регулярки), не LLM. `openai` и `live` **отправляют текст OCR чека внешнему провайдеру** (OpenAI / Anthropic) — на демо и в eval только синтетика, реальные чеки подавать нельзя. `auto`: известный sha256 чека → фикстуры (офлайн), неизвестный → живой Tesseract + OpenAI (если есть ключ) иначе rule-based baseline.

**Приватность:** файлы на диске под uuid-именами (оригинальные имена не сохраняются); содержимое документов и тела запросов не логируются; удаление дела есть (кнопка «Удалить дело» / `DELETE /cases/{id}`, удаляет записи и файлы). **Срок хранения/авто-удаления в коде не реализован** — файлы живут, пока дело не удалят вручную; политику хранения нужно определить (см. открытые вопросы в [docs/PLAN.md](docs/PLAN.md)). Сохранение ответов модели в `eval/fixtures/{sha}.json` включается только явно (`SAVE_LLM_FIXTURES=1`).

## Документация
- [docs/HANDOFF.md](docs/HANDOFF.md) — установка и запуск по шагам.
- [docs/PLAN.md](docs/PLAN.md) — статус, что реализовано/не реализовано, открытые вопросы, журнал.
- [docs/DECISIONS.md](docs/DECISIONS.md) — принятые решения и что урезано, с причинами.
- [docs/PLAN_TODAY.md](docs/PLAN_TODAY.md) — журнал по дням.
- [docs/E2E.md](docs/E2E.md) — сквозные сценарии (WhatsApp и Telegram).
- [frontend/docs/design.md](frontend/docs/design.md) — дизайн-система фронтенда.
- [CLAUDE.md](CLAUDE.md) — правила проекта и правила для продолжения работы.

## Стек
Python 3.14 (3.11+), FastAPI, SQLModel + SQLite, Pydantic, PyMuPDF, docxtpl, Pillow, pytesseract; React + Vite + TypeScript + Tailwind v4; LibreOffice (headless) для PDF.

## Инварианты (нарушать нельзя)
LLM возвращает только значения и `line_ids`; текст и координаты копирует код. Правовые нормы — только из `rules/legal_refs.json`. Поле попадает в претензию лишь при `confirmed_by_user=true`. Guard блокирует экспорт при любом числе или дате вне подтверждённых фактов и дат событий.

---
**Следующему человеку (и его ИИ): перед правками прочитай [CLAUDE.md](CLAUDE.md) и [docs/PLAN.md](docs/PLAN.md).**
