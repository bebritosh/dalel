# DÄLEL — фронтенд

React + Vite + TypeScript + Tailwind v4 + react-router.

## Запуск
```
npm install
npm run dev        # http://localhost:5173
```
По умолчанию `VITE_API_MODE=http` — фронтенд ходит на бэкенд через прокси `/api → http://127.0.0.1:8000`.

Режим без бэкенда (демо на синтетических данных):
```
VITE_API_MODE=mock npm run dev
```

## Скрипты
- `npm run build` — tsc + vite build
- `npm run typecheck` — проверка типов
- `npm run lint` — ESLint
- `npm run screenshots` — скриншоты через Playwright (нужен запущенный dev-сервер)

## Экраны
1. `/` — загрузка файлов, выбор типа, «Разобрать».
2. `/case/:id/review` — поля чека (править/подтверждать), хронология, «Чего не хватает».
3. `/case/:id/claim` — текст претензии с кликабельными суммами/датами и подсветкой строки на чеке; скачивание DOCX.

Токен дела хранится в `sessionStorage` (`case:{id}`); на экран кейса можно зайти с `?token=...`.

## Почему нет PDF
Экспорт PDF в этой версии не реализован: он требует LibreOffice на сервере. Бэкенд всегда отдаёт DOCX. Кнопки PDF на фронте нет осознанно.

## Про mock-данные
В mock-режиме данные синтетические (`src/mock`, `public/mock/receipt-001.svg`). Это демо-данные генератора, а не результат реального распознавания.
