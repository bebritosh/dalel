# DÄLEL — jury Q&A (EN, short, honest)

Placeholders `{{...}}` are filled from the real eval run. Do not quote a number you did not run.

## Required questions

**How is this better than ChatGPT?**
A general chat can write a nice letter, but it can also change a date or an amount and you will not notice. DÄLEL links every amount and date to a line of your receipt, requires your confirmation, and blocks the export if any number or date is not a confirmed fact. It also shows what evidence is missing. We have not run a systematic comparison with a general chat, so we do not claim a number for it.

**What if OCR is wrong?**
It will sometimes be. That is why nothing enters the claim until the user confirms the field, and the user sees the highlighted receipt line next to the value. Fields that cannot be read are shown as "not recognized", not guessed. On {{EVAL_N_CASES}} synthetic receipts the total amount was correct in {{EVAL_TOTAL_ACC}}%; the errors are what the confirmation step is for. Blurry real-world photos will be worse, and we have not measured them.

**What about personal data?**
The demo uses only synthetic data. Locally the files stay on the machine. In the live extraction mode the OCR text of the receipt is sent to an external model provider (OpenAI), so real receipts must not be used until consent, a data-processing agreement and a deletion flow are in place. The app has a delete-case function. Compliance with Kazakhstan personal-data law has not been reviewed by a lawyer yet.

**Is this legal advice?**
No. The interface says so. DÄLEL organizes the user's own evidence and prepares an editable draft that the user reviews. It does not assess whether the user will win and does not choose a legal strategy.

**Where do the legal norms come from?**
Today, from a fixed file with placeholders marked "to be clarified by a lawyer". We deliberately did not put in article numbers or quotes, because we have not verified them against the primary source. The model is not allowed to write legal references. Next step: a lawyer reviews and fills the file, with a source and a review date for each entry.

**Is the OCR live or fixtures?**
Both, and the interface shows which. The demo receipt uses saved results (fixtures) so that the demo is reliable and works offline. A new receipt goes through live Tesseract OCR and the extractor. The source badge on the review screen says "Fixture", "Live OCR" or "Live LLM". The fixtures were generated from our own synthetic receipt and are not presented as OCR results. The evaluation numbers come from the live path on {{EVAL_N_CASES}} synthetic cases.

## More likely questions

**What is the business model?**
Not validated yet. Candidates: free for consumers with partnerships (legal clinics, consumer associations, municipal services); paid tools for law firms and associations that handle many cases; a white-label version for marketplaces or sellers who want to resolve disputes earlier. We have not tested willingness to pay; the pilot will.

**How does it link to the SDGs?**
SDG 16.3 (access to justice): the first step of a dispute, a structured evidence file and a draft claim, becomes possible without a lawyer. SDG 12 (responsible consumption): disputes become easier to document and communicate. We do not claim social impact yet; we measure accuracy and time now, and outcomes in a pilot.

**What about Kazakh?**
Today the interface is Russian and English, and the claim text is Russian. Tesseract can read Russian and Kazakh text if the language packs are installed, but we only evaluated Russian synthetic receipts. A Kazakh interface and claim template, with proper review, are on the list for after the pilot.

**Will it scale? Other dispute types?**
The MVP covers one scenario, defective goods, on purpose. The pipeline (documents, facts with sources, timeline, missing evidence, guarded claim) is generic, so services and online orders mostly need new rules and templates, not a new architecture. Limits today: one receipt format family, WhatsApp text exports only (no Telegram), no PDF export, SQLite.

**Who are your competitors?**
General AI chats and legal-template sites: they write text but do not trace facts to sources. Law firms and legal clinics: reliable but slow and costly for small claims. Marketplace complaint forms: limited to their own platform. We have not done a full market review; we compete on traceability and on the guard.

**Can the model make something up?**
The model returns only values and line ids; text and coordinates are copied by code. Values that cannot be found in the receipt lines stay "needs review". The guard checks the final text. On {{EVAL_N_CASES}} synthetic cases invented values were {{EVAL_HALLUCINATION}}%. This is not a proof for all inputs.

**Does it work on any receipt?**
We do not claim that. We tested on {{EVAL_N_CASES}} synthetic receipts with different noise levels. Real-world receipts (thermal paper, glare, other layouts) need a pilot.

**What is left to do?**
A lawyer review of the legal set, real-user pilot, more chat formats, Kazakh interface, consent and data-protection work, and a larger evaluation.
