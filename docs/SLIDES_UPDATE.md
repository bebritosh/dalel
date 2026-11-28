# DÄLEL — slide text updates (EN)

Source deck: `~/Downloads/DALEL_Hackathon_Registration_2026.pdf` (8 slides; the repo has no editable source, so this file is copy-paste wording).
Rule: no number goes on a slide unless it comes from a real run. The numbers below are filled from the real run of 25.11.2026: `python eval/run_eval.py --mode openai` (snapshot `eval/results/openai-20261125-1452.json`; 9 synthetic cases, live Tesseract `rus+eng`, OpenAI `gpt-5.4-mini`). If you rerun the eval, update them.

Honest notes for the speaker:
- The "2% not found in receipt text" is **1 of 58 values**: on the blurred receipt (case-008) OCR read the date as `12.05 2026` (dot lost), the model normalised it to `2026-05-12` (correct vs gold), and the code did not find that value verbatim, so the fact stayed **ungrounded / needs review**. Nothing was silently accepted.
- Weak spot: item names, 94% (case-009, small font: OCR read «Чехол» as «Yexon»). The rule-based baseline gets items right in only 50% of cases (vs 94% with the LLM); its total amount is also 100% on this set.
- The synthetic set is relatively easy for Tesseract; these are not numbers for real phone photos.

## Numbers (25.11.2026 run)

| Value | Meaning | Source |
| --- | --- | --- |
| `9` | number of synthetic cases in the run | eval |
| `100` | accuracy of the total amount field, % | eval |
| `98` | share of facts that match their cited receipt lines, % | eval |
| `2` | share of extracted values not found in the receipt text, % (target 0) | eval |
| `2.2` | median time from upload to claim, seconds | eval |
| `9 of 9` | substituted-amount tests blocked by the guard, "x of y" | eval |
| `100` | total-amount accuracy of the rule-based baseline, % (optional) | eval |

Always write "synthetic" next to any number. Never write "works on any receipt".

---

## Slide 2 — The problem

Current card: "9,064 consumer appeals in Almaty, January–June 2026 / Official Committee for Consumer Protection data / Source: Ministry of Trade and Integration of Kazakhstan, H1 2026".

**QUESTION FOR THE USER (blocking for this slide):** I could not find the source of "9,064" anywhere in the repo, and I cannot verify it. Please confirm the exact document or page (gov.kz / Consumer Protection Committee, H1 2026) and that the figure is "appeals in Almaty" and not another unit or region. Also confirm whether "Official Committee ... data" and "Ministry of Trade and Integration" are the correct bodies. If you can open the page, keep the number and put the direct URL in the footer.

**Option A — keep (only after the user confirms the source):** leave the card as is; footer: "Source: <exact document title>, <URL>, accessed <date>."

**Option B — replacement without the number (use if not confirmed):**
- Big text: "The evidence exists. It is just not usable."
- Sub-label: "Receipts are photos. Disputes happen in chats. Claims need dates and amounts."
- Small print: "Illustrative scenario, not a statistic."
- Drop the "Source: Ministry..." line; keep only sources you actually checked on slide 8.

---

## Slide 4 — Grounded by construction (technology)

Keep the title and the subtitle "AI proposes structure. Code checks evidence. The user confirms facts."

Left card (fix the example to match the demo receipt):
- "SOURCE · RECEIPT IMAGE"
- "Smartphone X 128GB"
- "Total 249 990 ₸" (highlighted row)
- Label: "OCR LINE" (not "OCR BOX 08"; the demo receipt total is not on line 08 of the generator layout, so do not print a line number unless the UI shows the same number).

Middle card: "EXTRACTED FACT · Amount · 249 990 ₸ · LINE VERIFIED" ("LINE VERIFIED" instead of "LINE 08 VERIFIED").

Right card: "EXPORT GATE · Pass only if: source-linked & user-confirmed. Any number or date not backed by a confirmed fact blocks the export."

Bottom line, replace "No fabricated legal references: use a fixed, reviewed rule set." with:
"The model returns only values and line ids. Code copies text and coordinates. Legal references come from a fixed file, pending lawyer review. Nothing is invented."

New strip under the cards (only after the eval run; "N synthetic cases" label is mandatory):
> **Measured on 9 synthetic receipts (live Tesseract OCR + extractor):**
> total amount correct in 100% · facts grounded to a receipt line 98% · unverified values 2% (1 of 58, flagged for review) · substituted amount blocked by the guard: 9 of 9

Footnote: "Synthetic data only. Not a claim about real-world receipts."

If the baseline number is available, add: "Rule-based baseline for comparison: 100% on the same cases."

---

## Slide 5 — Prototype / MVP

Badge (top): replace "PLANNED MVP" with "WORKING PROTOTYPE".
Title: keep "One dispute. One complete journey."
Subtitle: keep "A defective-goods claim is the only mandatory hackathon scenario." (or "One scenario, end to end: receipt + chat → verified claim.")

Footer line: replace "Concept UI · Not a completed prototype · Demo data is synthetic" with
**"Working prototype · synthetic data"**

Demo data: recommendation is to change the slide to match the generator (`scripts/make_demo.py`, `eval/cases/demo-001/chat.txt`). Exact values from the generator:
- Seller: ТОО «Пример Электроникс» (English on the slide: "Sample Electronics LLP", keep the Russian name in the claim)
- Receipt No. 000123, 05.11.2026 14:32, item "Смартфон X 128GB" (English: "Smartphone X 128GB"), total 249 990,00 KZT
- Chat: 06.11 buyer writes about a flickering, overheating screen (first contact); 08.11 buyer sends a photo and asks for a refund; 09.11 seller refuses ("not a warranty case")

Card 01 "Upload evidence": "+ Receipt photo / PDF" and "+ Chat transcript" stay. Tag: "SYNTHETIC CASE".

Card 02 "Review timeline" (replace the three events; the app builds purchase, first contact and refusal from the files):
- 05 NOV · Purchase · "Receipt · highlighted line"
- 06 NOV · First contact · "Chat · buyer message"
- 09 NOV · Refusal · "Chat · seller message"

Do not show a "Defect" event with "Customer note": the app does not create one. Instead the "What is missing" list asks for a defect photo/video (rule M3) and warranty data (M1).

Card 03 "Export claim" (replace the text):
- "CONSUMER CLAIM"
- "Purchase: 5 Nov 2026"
- "Amount: 249 990 ₸"
- "Seller: Sample Electronics"
- Button: "REVIEW & EXPORT" (the app downloads DOCX)

Add a small badge in card 01 or the footer if the auto mode and source badge ship: "Source badge: Fixture / Live OCR / Live LLM". Say nothing about it on the slide if the badge is not in the final build.

Do not write: "works on any receipt", "fully automatic", "PDF export".

---

## Slide 6 — Purpose and metrics

Keep the SDG cards (SDG 16.3 and SDG 12). Change the heading "WHAT WE WILL MEASURE" to **"WHAT WE MEASURED · 9 synthetic cases"** (only once the run exists; otherwise keep "WHAT WE MEASURE" and show no numbers).

Three tiles (same names as now, plus the numbers):
1. "Extraction accuracy · dates, prices, seller" — "Total amount: 100%" (the per-field table goes into the speaker notes or a backup slide).
2. "Source coverage · facts linked to files" — "Grounded facts: 98% · unverified values: 2% (1 of 58, flagged for review)"
3. "Preparation time · upload to claim" — "Median 2.2 s with the tool" (computed in the eval run; do not add a "manual" figure, we have not measured it).

Sub-line under the tiles: "Synthetic receipts generated by us. Real-user results will come from a pilot."

Subtitle stays honest: "We measure useful outcomes — rather than claiming social impact before a pilot."

---

## Slide 7 — Team and delivery

Title: replace "A narrow scope. A five-hour build." with
**"A narrow scope. A working MVP."**

Subtitle: keep "Two student builders, one demo-ready evidence-to-claim flow."

Right-hand card "NOVEMBER 29 · HACKATHON EXECUTION" — replace the 00–25m / 25–140m / 140–200m / 200m+ rows with:
- Card header: "BEFORE THE EVENT"; row: "MVP built: backend, UI, evaluation on synthetic cases"
- Card header: "NOVEMBER 29 · EVENT DAY"; rows: "Polish" · "Pilot feedback" · "Live demo"

One-line version if the card has to stay small: "MVP built before the event; event day = polish, pilot, demo."

Roles: keep A (Data & validation: FastAPI · OCR · field extraction · source links · tests) and B (Product & demo: React · case timeline · document preview · presentation).

Footer stack line, replace "Planned stack: FastAPI · React · SQLite · OCR · LLM API · DOCX/PDF" with:
**"Stack: FastAPI · React · SQLite · Tesseract OCR · LLM API (strict JSON schema) · DOCX"**
(Say "DOCX" only: there is no PDF export. Mention the specific LLM, "OpenAI gpt-5.4-mini", only if the live extractor really ran in the final build.)

Optional privacy footnote: "In the demo only synthetic receipt text goes to the external model."

---

## Other small edits (not requested, flagged)
- Slide 1: the mock card says "Source Receipt · Line 08". Same remark as slide 4: use "Source · Receipt line" or a number that matches the UI.
- Slide 3: "EXPORT — Editable claim" is correct (DOCX). No change needed.
- Slide 8: "NOW · Working evidence-to-claim MVP" is fine once slide 5 says "working prototype". "multilingual UI": the UI already has RU/EN; Kazakh is not done, so keep it under LATER. Sources line: keep only sources you have actually opened.
