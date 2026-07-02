# Architecture

## System overview

```
Citizen Web App (Next.js 15, TypeScript, Tailwind, Recharts)
    |
    v
FastAPI API Gateway (apps/api/app/main.py)
    |
    +--> Text/Transcript Processor          (routers/cases.py: message + transcript ingestion)
    +--> Audio Transcription Adapter        (services/media.py: Whisper API or labelled mock)
    +--> OCR and QR Processor               (services/media.py: Tesseract / pyzbar or labelled mock)
    +--> Entity Extraction Engine           (engine/entities.py)
    +--> Coercion Sequence Detection Engine (engine/signals.py + engine/risk_engine.py)
    +--> Risk Fusion & Explainability       (engine/risk_engine.py: summarise/confidence/category)
    +--> Fraud Graph Service                (services/graph.py: NetworkX analysis)
    +--> Evidence Report Generator          (services/report.py: ReportLab PDF + SHA-256)
    +--> Audit Service                      (services/audit.py: append-only)
    |
    v
SQLite (default) / PostgreSQL via DATABASE_URL
    Cases · ConversationMessages · EvidenceFiles · ExtractedEntities
    RiskEvents · RiskAssessments · FraudGraphNodes/Edges · EvidenceReports
    AuditLogs · ReviewDecisions · ReportedEntities
```

## Risk engine design (the core differentiator)

The engine is **hybrid and deterministic** — no LLM makes the decision:

1. **Signal rules** (`engine/signals.py`): 17 signals across 13 coercion stages
   (lure, authority impersonation, identity-misuse claim, accusation, escalation,
   isolation, secrecy, continuous call, time pressure, threat, payment/OTP/remote
   access, confirmation pressure, evidence deletion). Each has EN + HI regex
   patterns, a weight, and a human-readable explanation in both languages.
2. **Awareness guards**: patterns like "never share your OTP" suppress signals in
   educational/awareness messages, which is what keeps genuine bank-awareness
   SMS at Low risk (false-positive control).
3. **Sequence bonuses**: eight stage-pair bonuses (e.g. *arrest threat → safe-account
   request* +20) awarded once when stages occur in scam-typical order. The same
   sentence in isolation scores less than the same sentence arriving after the
   coercion build-up.
4. **Repetition dampening**: repeated signals decay by 0.4^n so keyword spam
   cannot saturate the score.
5. **Speaker awareness**: only counterpart ("caller") messages carry coercion
   weight — a victim describing the scam does not inflate their own risk.
6. **Entity reputation**: identifiers found in the (synthetic) reported-entity
   registry add +15 once each.
7. **Normalisation**: the raw weighted sum maps to 0–100 against a ceiling of
   130, then into severity bands (see `packages/shared/severity.json`).
8. **Confidence**: grows with the number of distinct corroborating stages and
   awarded sequence bonuses, capped at 0.55 for single-message inputs.

Every point in the final score traces back to a persisted `RiskEvent` row, which
is what makes the assessment auditable and the PDF report defensible.

## Data flow for the live simulation

`POST /api/cases/{id}/messages` appends one message, then **re-runs the full
conversation** through a fresh engine state. This keeps the engine pure/testable
and guarantees the timeline is consistent after edits, re-analysis or transcript
merges. At demo scale (≤200 messages) this is O(messages × signals) and returns
in single-digit milliseconds.

## Trade-offs and deliberate choices

- **SQLite + `create_all` instead of Alembic migrations** — the prototype targets a
  reproducible single-file demo; PostgreSQL is a connection-string change and
  migrations would be the first production hardening step.
- **Custom SVG force layout instead of Cytoscape/React Flow** — no heavy graph
  dependency for a demo-sized network; the layout is ~80 lines and renders the
  ring structure clearly.
- **Schematic India SVG instead of Leaflet tiles** — the demo must work offline;
  a tile server dependency would violate "reliable without external services".
- **Static demo token instead of real auth** — explicitly labelled in the UI and
  threat model; role separation is demonstrated without pretending to be secure.
