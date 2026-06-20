# BillBuddy

**Plain-English explanations for Indian financial documents.**

Most people in India receive electricity bills, mobile bills, salary slips, and bank statements they don't fully understand — so they pay without questioning, or ignore them entirely. BillBuddy reads any such document and explains it in plain English: what every charge means, whether anything looks unusual, and a clear "should I be worried?" verdict at the top. It also answers follow-up questions about the document.

> **Status:** 🚧 In active development. Architecture and tech decisions are locked; core pipeline is being implemented function by function. See [Roadmap](#roadmap).

---

## Why this exists

Financial documents are written for the institutions that issue them, not the people who receive them. A non-technical person looking at an electricity bill can't easily tell a normal charge from an error, or a routine fee from something worth disputing. BillBuddy is built for exactly that person — someone who isn't tech-savvy and just wants to know *"is this fine, or do I need to do something?"*

That target user drives every design decision below.

## What it does (V1)

- **Upload a bill or statement** — PDF or phone photo.
- **Plain-English breakdown** of every line and section.
- **Flags unusual or unexpected charges** with a one-line "why."
- **A verdict box at the top** — `fine` / `check this` / `worrying` — so the answer is visible before reading anything else.
- **Follow-up Q&A** — ask questions about the document without re-uploading it.

## How it works

A document's journey from upload to answer:

```
React frontend  →  FastAPI endpoint  →  Detection step  →  ┬─ Text route (clean PDF)
                                                            └─ Vision route (photo / scanned PDF)
                                                                      ↓
                                          Model wrapper (analyze_document)
                                                                      ↓
                                          Schema-enforced JSON contract
                                                                      ↓
                            Session memory (follow-up Q&A)  →  Rendered result
```

**The routing step is the core architectural idea.** Each upload is sent down the cheapest path that can read it accurately:

- **Clean PDF** → extract the text layer directly. Cheap, exact, no AI needed for the text.
- **Photo or image-only PDF** → send straight to a vision model. *No OCR preprocessing step* — OCR on messy phone photos is too fragile for a finance app, where a single wrong number destroys trust.

A detection heuristic decides which path each file takes by checking whether a PDF has a trustworthy text layer.

**The JSON contract is the load-bearing wall.** The model is forced to return schema-enforced structured output (no regex parsing), including a `confidence` field that acts as an honesty guardrail — if a photo was blurry, the app says *"double-check the total yourself"* instead of confidently reporting a wrong number.

**The model sits behind a swappable wrapper.** A single `analyze_document(input) → result` function hides the model call, so swapping models is a one-line change — useful both as a portfolio talking point and as a mitigation for the wrong-number risk (A/B different models in minutes).

## Tech stack

| Layer | Choice |
|---|---|
| **Backend** | FastAPI (file upload → route → model → JSON) |
| **Frontend** | React + Tailwind CSS (mobile + desktop) |
| **Primary model** | Gemini 2.5 Flash-Lite (vision-capable, structured output, cheapest tier) |
| **Fallback model** | Claude Haiku 4.5 |
| **PDF handling** | PyMuPDF |
| **Gemini SDK** | `google-genai` (the unified Google Gen AI SDK) |
| **Session state** | In-memory dict (V1 — stateless, no database) |
| **Deployment** | Render (backend) + Vercel (frontend) |

Models are routed by task: the cheapest model that passes the accuracy bar handles each document. Cost works out to roughly **$0.0007 per document** on the primary model — the real operational risk is a runaway request loop, not per-document cost, so rate-limiting matters more than the spending cap.

## Document scope

Built in sequence rather than all at once, so each type can be made genuinely excellent before moving on:

- **V1** — Electricity bills + mobile/telecom bills (structurally similar, shared JSON shape)
- **V1.5** — Salary slips
- **V2** — Bank statements (the hard one: long documents, many transactions)

Document types are auto-detected, then confirmed by the user (*"I think this is an electricity bill — correct?"*) — zero friction for the common case, with a fix for rare misclassification.

## Project structure

```
bill-buddy/
  app/
    __init__.py
    main.py         # FastAPI app + endpoints
    routing.py      # detect_route, extract_text_layer, Route enum
    session.py      # store_document, get_document
    analyzer.py     # analyze_document model wrapper       (planned)
    contracts.py    # JSON contract / response schema      (planned)
  .env.example
  .gitignore
  requirements.txt
```

## Getting started

> Requires Python 3.12.

```bash
# clone and enter
git clone <repo-url>
cd bill-buddy

# create and activate a virtual environment
python -m venv venv
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate

# install dependencies
pip install -r requirements.txt

# configure secrets
cp .env.example .env   # then add your GEMINI_API_KEY / ANTHROPIC_API_KEY
```

## Roadmap

- [x] Architecture and data flow
- [x] Model selection + cost verification
- [x] Repo scaffold, virtual environment, env config
- [ ] Core routing + session functions
- [ ] JSON contract finalized
- [ ] `analyze_document` model wrapper
- [ ] FastAPI endpoints wired end to end
- [ ] React frontend
- [ ] Deployment (Render + Vercel)
- [ ] Hindi support (V2)

## Design notes

A few decisions worth calling out, because they're deliberate:

- **No OCR step.** Vision models read messy real-world photos better than an OCR-then-parse pipeline, and one wrong digit in a finance explainer is worse than no answer.
- **No database in V1.** The app is stateless — process, return, forget. Storage gets added only when month-over-month comparison (V2) actually requires it. Fewer stored secrets, less to leak.
- **English first, Hindi later.** Get extraction, structured output, and verdict logic correct and verifiable before adding a language that would require re-verifying all of it.
- **A `confidence` field instead of false certainty.** The single biggest risk in a finance explainer is confidently reporting a wrong number; the contract is designed so the app can admit uncertainty.

---

*Built as a portfolio project exploring multimodal input, schema-enforced structured output, domain-specific prompting, and a model-agnostic abstraction layer.*