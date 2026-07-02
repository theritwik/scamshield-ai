# ScamShield AI

**Detect coercion. Interrupt fraud. Protect before payment.**

AI-powered Digital Arrest Scam Defence & Fraud Intelligence platform for India — a hackathon prototype.

Digital-arrest scammers impersonate the CBI, ED, police, customs and banks, then trap victims through fear, isolation, secrecy and continuous video calls until money moves to a "safe account". Keyword tools miss this because **no single sentence is the scam — the sequence is the scam**. ScamShield AI detects the evolving sequence of psychological coercion across the whole conversation and interrupts the fraud before payment.

## Key innovation

A **sequence-aware, explainable coercion engine** (no LLM in the decision loop):

- 17 weighted signals across 13 coercion stages, in **English and Hindi**
- **Sequence bonuses** when stages occur in scam-typical order (arrest threat → safe-account demand: +20)
- Repetition dampening, speaker-aware scoring and **awareness-message guards** (a genuine "your bank never asks for OTP" SMS stays Low risk)
- **Entity reputation**: phones/UPI IDs/accounts already reported in other complaints raise the score — every complaint strengthens the next detection
- Every point of the 0–100 score traces to a persisted, named `RiskEvent` — which is what makes the PDF evidence report auditable

## Features

| Module | What it does |
|---|---|
| Citizen Fraud Shield | Paste text, simulate a call line-by-line, upload screenshots/audio/QR/transcripts, check a phone/UPI/account |
| Progressive risk timeline | Per-message signals, risk delta, cumulative score, click-to-explain |
| Explainable analysis | Score, severity, confidence, category, stage sequence, top evidence, missing evidence, false-positive caution, engine version |
| Safety Mode | Full-screen STOP guidance (EN/HI) that fires automatically at Critical risk |
| Multimodal ingestion | OCR (Tesseract), QR decode (pyzbar), Whisper transcription adapter — each with a clearly-labelled mock fallback so the demo needs no keys |
| Entity extraction | Phones, UPI IDs, accounts, IFSC, URLs, emails, amounts, agencies, remote tools — masked by default |
| Fraud network graph | Complaints linked via shared identifiers; connected components, centrality, suspected-mule ranking, plain-language insights |
| EvidenceChain report | One-click PDF: case ID, timestamps, consent, coercion sequence, transcript excerpts, masked entities, SHA-256 hashes, audit trail, disclaimers |
| Command Centre | Case queue, review workflow, watchlist, emerging-script analytics, synthetic hotspot map, global audit trail (demo-token gated) |
| Auditability | Append-only audit log for case/evidence/analysis/report/review events |

## Demo flow

See [docs/demo-script.md](docs/demo-script.md) for the 3–4 minute walkthrough. Short version: **Live Demo → ▶ Play scripted scam call** and watch the risk climb 12% → 27% → 54% → 75% (Safety Mode fires) → 100%, then generate the PDF evidence report and open the Command Centre fraud graph to see the mule ring.

## Architecture

Next.js 15 (TypeScript, Tailwind, Recharts) → FastAPI (Python, SQLAlchemy, Pydantic) → SQLite/PostgreSQL, with NetworkX for graph analysis and ReportLab for PDFs. Full details and trade-offs: [docs/architecture.md](docs/architecture.md).

## Setup

Prerequisites: Python 3.11+, Node 20+. Optional: Tesseract + libzbar for real OCR/QR (mocks used otherwise).

```bash
# 1. Install
pip install -r apps/api/requirements.txt
cd apps/web && npm install && cd ../..

# 2. Seed synthetic demo data (20 fictional complaints incl. a visible fraud ring)
python3 scripts/seed_data.py

# 3. Run (two terminals)
make api    # FastAPI on :8000  (OpenAPI docs at /docs)
make web    # Next.js on :3000
```

Or with Docker: `docker compose up --build`, then seed inside the container or run the seed script against the mounted volume.

### Environment variables

Copy `.env.example`. Everything has a working default; the demo needs **no keys**.

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy URL | SQLite file |
| `CORS_ORIGINS` | Allowed origins | `http://localhost:3000` |
| `INVESTIGATOR_DEMO_TOKEN` | Demo dashboard token | `demo-investigator` |
| `OPENAI_API_KEY` | Optional real Whisper transcription | unset → labelled mock |
| `NEXT_PUBLIC_API_URL` | API base for the web app | `http://localhost:8000` |

## Testing & evaluation

```bash
make test    # 27 pytest tests: risk engine, entities, full API flow
make lint    # ESLint + Next.js production type-check build
make eval    # keyword baseline vs sequence engine → data/evaluation/results.{json,md}
```

All published metrics come from `scripts/evaluate.py` on the synthetic labelled dataset — the README intentionally cites none that the script did not produce. See [data/evaluation/results.md](data/evaluation/results.md) after running.

## API

FastAPI auto-generates OpenAPI docs at `http://localhost:8000/docs`. Main endpoints: `POST /api/cases`, `POST /api/cases/{id}/messages` (incremental analysis), `POST /api/cases/{id}/evidence`, `GET /api/cases/{id}/risk-timeline`, `POST /api/cases/{id}/generate-report`, `GET /api/graph/network`, `GET /api/dashboard/summary`, `GET /api/audit/{case_id}`, `GET /api/health`.

## Privacy & limitations

This is a prototype: it does **not** intercept live calls, block accounts, contact police, or detect AI voices. Alerts are simulated and labelled. Consent is required per case, identifiers are masked, uploads are SHA-256 hashed and never altered, the audit log is append-only, and all complaint data is synthetic. Details: [docs/privacy.md](docs/privacy.md), [docs/model-card.md](docs/model-card.md), [docs/threat-model.md](docs/threat-model.md).

## Deployment

- **Frontend** → Vercel (`apps/web`, set `NEXT_PUBLIC_API_URL`)
- **Backend** → Render/Railway (`apps/api`, Dockerfile provided; set `DATABASE_URL` to managed PostgreSQL and `CORS_ORIGINS` to the Vercel URL)
- **Local full stack** → `docker compose up --build`

## Future roadmap

Semantic script-similarity clustering (sentence-transformers), romanised-Hindi/Hinglish coverage, more Indian languages, Neo4j-backed graph at volume, bank-app SDK for in-flow payment interruption, real 1930-helpline handoff with partner agencies, and a human-in-the-loop rule-update pipeline.

## Hackathon judging alignment

Mapped point-by-point in [docs/judging-alignment.md](docs/judging-alignment.md).
