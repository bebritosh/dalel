# DÄLEL — 5-minute pitch (EN)

Total target: 4:55 (5 s buffer). Slide numbers follow the current deck (8 slides). Wording of slides: see `SLIDES_UPDATE.md`.
Numbers in `{{...}}` come only from the real eval run. If a number is missing, skip the sentence. Say "synthetic" every time you give a number.

| Slide | Time | Cumulative |
| --- | --- | --- |
| 1 Title | 0:20 | 0:20 |
| 2 Problem | 0:30 | 0:50 |
| 3 Solution | 0:30 | 1:20 |
| 4 Technology | 0:40 | 2:00 |
| 5 Prototype + live demo | 1:30 | 3:30 |
| 6 Metrics and SDG | 0:35 | 4:05 |
| 7 Team and delivery | 0:25 | 4:30 |
| 8 Next steps | 0:25 | 4:55 |

---

## Slide 1 — Title (0:20)
"Hello. We are DÄLEL. A person buys a phone, it breaks, the seller refuses in a chat. They have proof, but it is a photo of a receipt and a chat export. DÄLEL turns that into a claim you can verify. We work on two goals: access to justice, SDG 16.3, and responsible consumption, SDG 12."

## Slide 2 — Problem (0:30)
"The problem is not that people have no evidence. It is that the evidence is scattered. The receipt is a photo. The defect is in a message. The refusal is in a chat. To write a claim, a person has to find every date and amount and put them in one document, without mistakes. Most people give up at this first step, or pay for help they cannot always afford."
- If the 9,064 figure is confirmed (see SLIDES_UPDATE.md, slide 2): add "In Almaty alone, the Consumer Protection Committee recorded 9,064 appeals in the first half of 2026." Otherwise skip this sentence.

## Slide 3 — Solution (0:30)
"DÄLEL is a case file, not another chatbot. You upload the receipt and the chat. The system extracts dates and amounts, links each one to the exact line of the original file, shows you what is still missing, and prepares an editable claim. You confirm every fact before it can enter the document. Our promise: every important amount and date links back to the original file."

## Slide 4 — Technology (0:40)
"Why you can trust the draft. Three rules, enforced in code. One: the model only proposes values and line numbers. Code copies the text and coordinates from the OCR. Two: a field enters the claim only after the user confirms it. Three: an export gate scans the claim, and any number or date that is not a confirmed fact blocks the export. Legal references are not written by the model. They come from a fixed file, and today they are placeholders until a lawyer reviews them. We do not invent articles."
- With eval: "On {{EVAL_N_CASES}} synthetic receipts, with live Tesseract OCR, the total amount was correct in {{EVAL_TOTAL_ACC}}%, facts were grounded to a receipt line in {{EVAL_GROUNDING}}%, and invented values were {{EVAL_HALLUCINATION}}%. When we substitute the amount, the guard blocked {{EVAL_GUARD_BLOCKED}}. These are synthetic receipts, not a claim about every receipt."

## Slide 5 — Prototype + live demo (1:30)
Say on the slide (10 s): "This is a working prototype on synthetic data. Let me show it." Then switch to the live demo (70–90 s, below), come back to the slide deck for slide 6.

### Live demo script (about 80 s; practise with a stopwatch)
Preparation: backend and frontend running, UI language EN, a fresh case page open, files `eval/cases/demo-001/receipt.png` and `chat.txt` in one folder on the desktop. Mode `auto` (the demo receipt uses fixtures, see QA).

| # | Time | Click | Say |
| --- | --- | --- | --- |
| 1 | 0:00 | Drag `receipt.png` into the zone typed "Receipt", `chat.txt` into "Chat". Click "Analyze". | "Our customer bought a smartphone for 249 990 tenge. The receipt is a photo, the dispute is in a chat. I upload both." |
| 2 | 0:10 | Review screen opens. Point at the source badge. | "The badge shows where the data came from. For this known demo receipt we use saved results for reliability; a new receipt goes through live OCR. Everything here is synthetic." |
| 3 | 0:20 | Click the amount in the fields list; the receipt line highlights. | "Each field is linked to its line on the receipt. Click the amount, the line lights up." |
| 4 | 0:30 | Click "Confirm" on seller, date, amount, currency, item. Point at "warranty: not recognized". | "I confirm what is right. The warranty period was not recognized, and the system says so instead of guessing." |
| 5 | 0:42 | Show the timeline: 5 Nov purchase, 6 Nov first contact, 9 Nov refusal. | "From the chat, the timeline is built automatically: purchase, first contact, the seller's refusal." |
| 6 | 0:52 | Show "What is missing" (warranty data, defect photo or video). | "And it tells me what I still lack: a defect photo and the warranty. This is what a lawyer would ask first." |
| 7 | 1:02 | Click "Go to claim". Click the amount in the text, receipt line highlights. | "The claim is ready. Every amount and date is a confirmed fact, and I can click any of them to see the source." |
| 8 | 1:12 | Click "Download DOCX". Open the file briefly. | "I export an editable DOCX. Legal references show as 'to be clarified by a lawyer', not invented." |
| 9 | 1:20 | (Only if the UI shows a blocked state; else skip) show the "Export blocked" message from a prepared case. | "If any number is not a confirmed fact, the export is blocked. That is our guard." |

Fallbacks: backend down → open the mock build (`VITE_API_MODE=mock`); everything down → play the recorded video. Say "this is the recorded run" if you switch.
Do not say: "works on any receipt", "AI knows the law", "the claim is legally valid".

## Slide 6 — Metrics and SDG (0:35)
"We measure outcomes, not social impact before a pilot. On {{EVAL_N_CASES}} synthetic cases: total amount accuracy {{EVAL_TOTAL_ACC}}%, grounded facts {{EVAL_GROUNDING}}%, invented values {{EVAL_HALLUCINATION}}%, and a claim in about {{EVAL_TIME_TO_CLAIM}} seconds from upload. For SDG 16.3 this lowers the barrier to the first step without a lawyer. For SDG 12 it makes consumer disputes easier to document. The real test will be a pilot with users."
- If the eval has not run, replace the numbers with: "We built an evaluation on synthetic receipts and we will show results once they are final." Better: do not mention it.

## Slide 7 — Team and delivery (0:25)
"We are two students. The MVP was built before the event: backend, OCR, extraction, the interface and the evaluation. On event day we focus on polish, pilot feedback and the demo. Stack: FastAPI, React, Tesseract OCR, an LLM API with a strict JSON schema, and DOCX export."

## Slide 8 — Next steps (0:25)
"Now: the defective-goods claim, working end to end. Next: a small pilot with consumers and legal clinics, and a lawyer's review of the legal reference set. Later: services, online orders, and more languages in the interface. DÄLEL: evidence people can act on. Thank you."

---

## Delivery notes
- The first 20 seconds must state the problem; the demo must start by 2:00.
- Never read numbers you cannot show. If eval numbers differ from the placeholders you planned, say the real ones.
- If the demo breaks, stay on the badge and the guard: "the point is that nothing enters the claim without a source and your confirmation".
