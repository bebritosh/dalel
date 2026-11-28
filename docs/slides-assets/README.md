# Slide assets (25.11.2026)

Screenshots taken with ego-browser at 1440×900 (2× DPR) on synthetic data only. Backend in `LLM_MODE=auto`.

| File | What it shows | Data source |
| --- | --- | --- |
| `01-upload.png` | Upload screen with consent and typed files | demo-001 (synthetic) |
| `02-review-fixture.png` | Review: fields with "needs review", timeline, missing evidence; badge **OCR: Fixture / Extraction: Fixture** | demo-001, fixtures (known sha) |
| `03-review-confirmed.png` | Review after confirming the fields | demo-001, fixtures |
| `04-claim-highlight.png` | Claim text; clicking the amount highlights the «ИТОГО» line on the receipt; response deadline wording | demo-001, fixtures |
| `05-review-live.png` | Unseen receipt through the live path; badge **Live OCR (Tesseract) / Live LLM (OpenAI)** + external-provider note | case-003 (synthetic), live |
| `06-eval-table.png` | Eval table, 9 synthetic cases, openai mode | `eval/results/openai-20261125-1452.json` |

Slides with 02–04 must say "fixture" (the badge is visible); use 05 to show the live path.
