# DÄLEL — как запустить (macOS и Windows)

## Что это
Прототип конструктора претензий по некачественному товару. Бэкенд (FastAPI) +
фронтенд (React/Vite). Данные демо синтетические. OCR и ответы LLM на демо берутся
из офлайн-фикстур (см. «Про фикстуры» ниже) — интернет не нужен.

## Требования
- Python 3.11+ (проект проверен на 3.13 на Mac и 3.14 на Windows). Системный `python3` на macOS = 3.9 — **слишком старый**, не использовать.
- Node.js 20+ (проверено на 24 и 26) и npm.
- Tesseract и LibreOffice НЕ нужны для демо на известном чеке (OCR из фикстур, экспорт только DOCX).
  Tesseract (с языком `rus`) нужен только для режимов, где OCR живой (новый чек).

Статус проверки: команды ниже для **macOS** проверены (Python 3.13 через `uv`, Node 26, npm 11).
Команды для **Windows** не проверены на Windows (перенесены с прошлой версии документа, где они были рабочими на Python 3.14.3): помечено «не проверено на Windows».

## Первая настройка (один раз)

### macOS (проверено)
Из корня репозитория. Нужен [`uv`](https://docs.astral.sh/uv/) (`brew install uv`) либо любой Python 3.11+.
```
uv venv --python 3.13 .venv
uv pip install --only-binary=:all: -r requirements.txt
```
Без `uv`, если есть Python 3.11+ (например `brew install python@3.13`):
```
/opt/homebrew/bin/python3.13 -m venv .venv
.venv/bin/python -m pip install --only-binary=:all: -r requirements.txt
```
(второй вариант не прогонялся; в `.venv` от `uv` модуля `pip` нет, поэтому там нужен именно `uv pip`).

### Windows (не проверено на Windows)
```
py -3 -m venv .venv
.venv\Scripts\python -m pip install --only-binary=:all: -r requirements.txt
```
Если `py` не найден — поставить Python 3.11+ с python.org (галочка «Add to PATH») и использовать `python -m venv .venv`.

### Фронтенд (обе системы)
```
cd frontend
npm install
```
(`npm ci` тоже подходит, он быстрее и берёт точные версии из `package-lock.json`, но сначала удаляет `node_modules`.)

### Файл `.env` (необязательно для демо на фикстурах)
Значения по умолчанию рабочие (`LLM_MODE=fixture`, `OCR_ENGINE=fixture`). Для живых режимов:
```
cp .env.example .env        # macOS;  Windows: copy .env.example .env
```
и заполнить нужное. `.env` не коммитить, ключи не печатать. Режимы `LLM_MODE` (`fixture`, `rules`, `openai`, `live`, `auto`) и `OCR_ENGINE` (`fixture`, `tesseract`, `auto`) добавляются в день 25.11: актуальный список и описание смотри в `.env.example`.

Переменные путей к внешним инструментам (нужны только для живых режимов; на демо не требуются):
- `TESSERACT_CMD` — путь к `tesseract.exe`, если он не в `PATH` (для `OCR_ENGINE=tesseract`/`auto` и для `eval/run_eval.py`). Без Tesseract eval не запускается — это ожидаемо.
- `SOFFICE_PATH` — путь к `soffice` LibreOffice для PDF-экспорта. Не задан или LibreOffice не установлен → эндпоинт `?format=pdf` отдаёт **503** с понятным текстом, приложение не падает; DOCX работает всегда.
- База не требует ручного удаления: при обновлении схемы недостающие колонки добавляются авто-миграцией на старте. Полный сброс — `python scripts/reset_db.py` (с подтверждением).

### Шаблон и фикстуры
Шаблон претензии (`templates/claim.docx`) и демо-фикстуры (`eval/fixtures/`, `eval/cases/demo-001/`) уже в репозитории.
**Не пересоздавать их на демо-машине.** Фикстуры привязаны к sha256 файла `eval/cases/demo-001/receipt.png`; перегенерация (`scripts/make_demo.py`) даёт другой PNG (шрифты зависят от ОС), хэш меняется и фикстуры перестают находиться. Запускать генератор только осознанно, если менялся сам генератор, и потом перепроверять сценарий:
```
.venv/bin/python scripts/make_claim_template.py      # Windows: .venv\Scripts\python scripts\make_claim_template.py
.venv/bin/python scripts/make_mock_exports.py        # после правок претензии/шаблона/legal_refs: DOCX/PDF/текст для mock-сборки
.venv/bin/python scripts/make_demo.py                # Windows: .venv\Scripts\python scripts\make_demo.py
```
Проверка, что демо-чек тот же: `shasum -a 256 eval/cases/demo-001/receipt.png` (macOS) должен начинаться с `eeef4d42540c...`; Windows: `certutil -hashfile eval\cases\demo-001\receipt.png SHA256` (не проверено на Windows).

## Запуск (3 команды)
Открыть два терминала.

### macOS (проверено: сервер стартует, `/docs` отвечает 200; первый старт может занять несколько секунд)
Терминал 1 — бэкенд, из корня репозитория:
```
.venv/bin/python -m uvicorn app.main:app --reload
```
Терминал 2 — фронтенд:
```
cd frontend
npm run dev
```

### Windows (не проверено на Windows)
Терминал 1 — бэкенд, из корня репозитория:
```
.venv\Scripts\python -m uvicorn app.main:app --reload
```
Терминал 2 — фронтенд, из `frontend`:
```
npm run dev
```

Открыть в браузере: `http://localhost:5173`

(Третья «команда» — открыть браузер. Бэкенд на `http://127.0.0.1:8000`, Swagger — `/docs`. Фронтенд проксирует `/api` на `127.0.0.1:8000`; если порт 8000 занят, бэкенд надо запускать с `--port 8000` на свободной машине или менять прокси в `frontend/vite.config.ts`.)

## Демо-сценарий
1. На экране «Новое дело» перетащить два файла из `eval/cases/demo-001/`:
   `receipt.png` (тип «Чек») и `chat.txt` (тип «Переписка»). Нажать «Разобрать».
2. На экране проверки подтвердить поля (минимум: продавец, дата покупки, сумма).
   Справа — хронология и «Чего не хватает».
3. На экране претензии: клик по сумме/дате подсвечивает строку на чеке.
   «Скачать DOCX» сохраняет претензию. «Отправлено продавцу» запускает таймер ответа (по умолчанию 10 дней, срок уточняется).

## Режим без бэкенда (для слайдов/жюри)
Dev-сервер без бэкенда (одна команда, одинаково на macOS и Windows, проверено на macOS):
```
cd frontend
npm run dev:mock
```
(Эквивалент `VITE_API_MODE=mock npm run dev`, но без синтаксиса переменных окружения, который различается в cmd/PowerShell/zsh. Режим берётся из `frontend/.env.mock`.) Если порт 5173 занят, vite выберет следующий (5174, 5175…): смотри адрес в его выводе.

### Статическая mock-сборка (бэкенд, Python и Node на целевой машине не нужны)
```
cd frontend
npm run build:mock
```
Результат: папка `frontend/dist-mock/` (в `.gitignore`, собирать надо на своей машине и везти на флешке). Открывать **через любой статический сервер из корня сайта**, например:
```
cd frontend/dist-mock
python3 -m http.server 8080          # Windows: python -m http.server 8080
```
и `http://localhost:8080/`. Либо `npm run preview:mock` в `frontend/`.
Проверено на macOS: главный экран, переход «Разобрать» → проверка → претензия с чеком и подсветкой работают без бэкенда. Ограничения:
- Открытие `index.html` двойным кликом (`file://`) **не проверено** и скорее всего покажет пустую страницу: роутер использует `BrowserRouter`, ему нужен http-адрес (для `file://` нужен `HashRouter` в `frontend/src/App.tsx` и правка пути к картинке чека; пока не сделано).
- Перезагрузка страницы (F5) на внутренних адресах `/case/1/review` и `/case/1/claim` в статическом сервере без SPA-fallback даёт 404 или пустую страницу. На демо не перезагружать, начинать с главной.
- Картинка чека берётся по абсолютному пути `/mock/receipt-001.svg`: сборка должна лежать в корне сервера, не в подпапке.
- Шрифт Inter подгружается с Google Fonts; без интернета подставляется системный шрифт, функциональность не страдает.
- В mock-режиме «Скачать DOCX» отдаёт текстовую заглушку, а не настоящий DOCX.

## Остальная документация
- [README.md](../README.md) — обзор и статус.
- [PLAN.md](PLAN.md) — фазы и открытые вопросы.
- [DECISIONS.md](DECISIONS.md) — решения, что урезано, про фикстуры.

## Тесты и оценка
- Тесты бэкенда: Windows — `.venv\Scripts\python -m pytest -q` (на этой машине **85 passed, 1 skipped** на 25.11; skip — конвертация PDF без LibreOffice). macOS — `.venv/bin/python -m pytest -q`.
- Проверки фронтенда: `cd frontend && npm run typecheck && npm run lint && npm run build && npm run build:mock`.
- eval: `.venv\Scripts\python eval\run_eval.py --mode rules` (офлайн, нужен Tesseract). `--mode openai` — нужен `OPENAI_API_KEY`.
- Скриншоты экранов: `frontend/screenshots/` (скрипт `npm run screenshots` требует браузеров Playwright: `npx playwright install`, один раз).

## Что установить для живых режимов (на демо-фикстурах не нужно)
- **Tesseract OCR** (языки `rus`+`eng`) — для `OCR_ENGINE=tesseract/auto` и для `eval/run_eval.py`. Если не в `PATH`, прописать путь в `.env`: `TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe`. Проверка: `tesseract --list-langs` показывает `rus` и `eng`.
- **LibreOffice** — для PDF-экспорта. Прописать `SOFFICE_PATH=C:\Program Files\LibreOffice\program\soffice.exe`. Без него PDF отдаёт 503 (DOCX работает).
- **OpenAI-ключ** — для `LLM_MODE=openai/auto` и openai-цифр eval: `OPENAI_API_KEY=...` в `.env`. `.env` не коммитить.

## Проверка на чистом Windows (ещё не делалась — см. «Открытые проблемы» в PLAN.md)
1. Клон репозитория, ветка с кодом.
2. `py -3 -m venv .venv` → `.venv\Scripts\python -m pip install --only-binary=:all: -r requirements.txt`.
3. `cd frontend && npm install`.
4. Бэкенд: `.venv\Scripts\python -m uvicorn app.main:app --reload` (на старте в логе — авто-миграция БД, удалять `data\dalel.db` не нужно).
5. Фронтенд: `npm run dev` → открыть адрес из вывода Vite (обычно 5173; может выбрать следующий свободный).
6. Демо-сценарий из раздела выше; отдельно — **открыть скачанный DOCX в Word** (ключевая ручная проверка, см. «Открытые проблемы»).

## Про фикстуры (честно)
- `eval\fixtures\{sha}.layout.json` — это РАЗМЕТКА генератора чека (истинные строки и
  координаты), а НЕ результат реального OCR. Так демо детерминировано и офлайн.
- `eval\fixtures\handmade_{sha}.json` — РУЧНОЙ ответ извлечения (нет ключа LLM на демо),
  помечен префиксом `handmade_` и полем `_source`. Это не реальный ответ модели.
- Живой OCR (Tesseract, `OCR_ENGINE=tesseract`) и живой LLM (`LLM_MODE=openai` / `live` / `auto`)
  подключаются переменными в `.env`, когда установлен Tesseract (macOS: `brew install tesseract tesseract-lang`, нужен язык `rus`: `tesseract --list-langs`) и есть ключ. В живых режимах текст чека уходит внешнему провайдеру: только синтетика.

## PDF-экспорт
Есть кнопка «Скачать PDF». PDF собирается конвертацией того же guard’ованного DOCX через
LibreOffice headless (`soffice`). Путь — в `SOFFICE_PATH`; если LibreOffice не установлен,
эндпоинт отдаёт **503** и UI показывает понятный текст — DOCX при этом работает всегда и
готов к печати. На демо без LibreOffice используйте DOCX.
