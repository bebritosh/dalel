# Видео-запись демо (70–90 с) — сценарий и список кадров

Запись делает пользователь. Это последняя ступень лестницы запасных вариантов (`docs/DEMO_RUNBOOK.md`). Сценарий совпадает со скриптом живого демо в `docs/PITCH.md` (слайд 5), чтобы можно было переключиться с живого на запись на любом шаге.

## Подготовка (до записи)
- Бэкенд и фронтенд запущены, режим на известном демо-чеке (`auto`/фикстуры; в UI видна плашка источника). Если записываешь живой режим на новом чеке, так и подпиши в кадре.
- Язык интерфейса EN (по плану питча), претензия остаётся на русском.
- Окно браузера 1920×1080 (или 1440×900 с масштабом 100%), панель закладок скрыта, лишние вкладки закрыты, уведомления выключены (macOS: режим «Не беспокоить»).
- Чистое состояние: тестовые дела удалены. В кадре не должно быть ключей, `.env`, терминала с токенами, личных данных.
- Файлы на рабочем столе: `receipt.png`, `chat.txt` (из `eval/cases/demo-001/`).
- Запись экрана: macOS — `Shift+Cmd+5` (встроенная запись, с микрофоном при озвучке) или QuickTime; Windows — `Win+G` (Xbox Game Bar) или OBS. Формат MP4, 1080p, 30 fps.
- Озвучка: либо голосом сразу, либо записать картинку без звука и наложить текст субтитрами. Субтитры на английском, ниже дублировать ключевые слова в кадре.
- Репетиция с секундомером 2–3 раза. Мышь двигать медленно и целенаправленно.

## Таймлайн (≈ 80 с)
| № | Время | Кадр / действие | Закадровый текст (EN) | Что должно быть видно |
| --- | --- | --- | --- | --- |
| 0 | 0:00–0:03 | Титр: «DÄLEL · working prototype · synthetic data» | — | Название, пометка про синтетику |
| 1 | 0:03–0:13 | Экран «Новое дело»: перетащить `receipt.png` (тип Receipt) и `chat.txt` (тип Chat), нажать «Analyze» | "Our customer bought a smartphone for 249 990 tenge. The receipt is a photo, the dispute is in a chat. I upload both." | Оба файла с типами, кнопка |
| 2 | 0:13–0:23 | Экран проверки; навести на плашку источника | "The badge shows where the data came from. For this demo receipt we use saved results for reliability. Everything here is synthetic." | Плашка «Fixture / Live OCR / Live LLM» крупным планом (приблизить) |
| 3 | 0:23–0:33 | Клик по сумме в списке полей, подсветка строки на чеке | "Each field is linked to its line on the receipt. Click the amount, the line lights up." | Подсвеченная строка ИТОГО |
| 4 | 0:33–0:45 | Нажать «Confirm» у продавца, даты, суммы, валюты, товара; показать «warranty: not recognized» | "I confirm what is right. The warranty period was not recognized, and the system says so instead of guessing." | Статусы «confirmed», поле без значения |
| 5 | 0:45–0:55 | Хронология: 5 Nov покупка, 6 Nov обращение, 9 Nov отказ | "From the chat the timeline is built automatically: purchase, first contact, the seller's refusal." | Три события с датами |
| 6 | 0:55–1:05 | Блок «What is missing»: фото/видео дефекта, гарантия | "And it tells me what I still lack: a defect photo and the warranty. This is what a lawyer would ask first." | Список недостающего |
| 7 | 1:05–1:15 | «Go to claim»; клик по сумме в тексте претензии, подсветка чека | "The claim is ready. Every amount and date is a confirmed fact, and I can click any of them to see the source." | Текст претензии и чек рядом |
| 8 | 1:15–1:23 | «Download DOCX», кратко показать открытый файл | "I export an editable DOCX. Legal references show as 'to be clarified by a lawyer', not invented." | Файл DOCX, пометка «[норма уточняется юристом]» |
| 9 | 1:23–1:30 | (Опционально, если есть подготовленное дело) состояние «Export blocked» | "If a number is not a confirmed fact, the export is blocked. That is our guard." | Сообщение о блокировке |
| 10 | 1:30–1:35 | Финальный титр: название, имена команды, контакт | — | Контакт |

Если укладываешься в 90 с без п. 9 — п. 9 вырезать. Целевая длина 70–90 с: пункты 0 и 10 по 3–5 с.

## Чего не говорить и не показывать
- Не говорить: «works on any receipt», «AI knows the law», «the claim is legally valid».
- Не показывать реальные чеки и персональные данные, `.env`, ключи, терминал с логами запросов.
- Если режим показывает фикстуры, не называть это «live OCR».
- Срок ответа продавца в кадре описывать как «по умолчанию 10 дней, уточняется», не как закон.

## Выдача
- Файл `dalel-demo.mp4` (до ~50 МБ), копия на двух флешках и в облаке.
- Запасная версия без звука с субтитрами (если на сцене нет звука).
- Проверить воспроизведение на чужом компьютере/плеере (VLC и системный).
