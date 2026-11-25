# E2E: сквозные сценарии DÄLEL

Полный путь дела для двух источников переписки — **WhatsApp (txt)** и
**Telegram (result.json)** — через API и через UI. Всё офлайн: `ocr_engine=fixture`,
`llm_mode=fixture`, **без `OPENAI_API_KEY`** и без Tesseract/LibreOffice.

Синтетические дела (данные полностью вымышлены):
- `eval/cases/demo-001/` — чек + `chat.txt` (WhatsApp).
- `eval/cases/demo-tg-001/` — тот же чек + `chat.json` (Telegram). Чек тот же → совпадает sha256 → применяются те же офлайн-фикстуры OCR/извлечения.

## API-путь (автотест)
`tests/test_e2e.py` прогоняет для обоих источников:
1. `POST /cases` → дело.
2. `POST /cases/{id}/documents` — чек (`receipt`) и переписка (`chat`: `.txt` или `.json`).
3. `POST /cases/{id}/extract` — поля `seller_name/purchase_date/total_amount/currency` c `grounded=true`.
4. `GET /cases/{id}/timeline` — события `purchase`, `contact`, `refusal` (+`reply`), каждое с `message_id`:
   - WhatsApp — `message_id` вида `line:N`;
   - Telegram — числовой `message_id`.
5. `PATCH /facts/{id}` — подтверждение обязательных полей.
6. `POST /cases/{id}/claim` — претензия (guard проходит).
7. `GET /cases/{id}/export?format=docx` — DOCX (сигнатура `PK`).

Отдельно проверено:
- `test_no_openai_key_in_test_env` — в тестовом окружении `openai_api_key == ""`.
- `test_e2e_rules_mode_offline` — извлечение в режиме `rules` поверх фикстурного OCR работает без ключа.

Запуск: `.venv/Scripts/python.exe -m pytest tests/test_e2e.py -q` → 4 passed.

## UI-путь (Playwright, 1440×900 и 390×844)
Бэкенд на `:8000` (fixture), Vite с прокси `/api`. Скрипт: `frontend/scripts/screenshots.mjs`.

- **WhatsApp:** `SHOT_MODE=http BASE=http://localhost:5174 node scripts/screenshots.mjs`
  → `frontend/screenshots/http-upload|review|claim-*.png`. На экране претензии — кнопки «Скачать DOCX» и «Скачать PDF» (PDF → 503 без LibreOffice, текст показывается, приложение не падает).
- **Telegram:** `SHOT_MODE=http CHAT_FILE=eval/cases/demo-tg-001/chat.json PREFIX=tg- BASE=... node scripts/screenshots.mjs`
  → `frontend/screenshots/tg-http-*.png`. В хронологии события `Обращение / Ответ продавца / Отказ` с плашкой источника **Telegram**.

Экран согласия и язык RU в скриншотах выставляются через `localStorage` (`dalel:consent=1`, `dalel:lang=ru`).

## Чего нет на этой машине (ожидаемо, не блок)
- **Tesseract** не установлен → `eval/run_eval.py` не запускается (нужен для OCR в любом режиме). Приложение работает на фикстурном OCR.
- **LibreOffice** не установлен → PDF-экспорт отдаёт 503 с понятным текстом; DOCX работает.
- **OPENAI_API_KEY** отсутствует → живой openai-путь не запускается; fixture и rules пути самодостаточны.
