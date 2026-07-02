# Judging alignment

## Innovation
- **Psychological captivity detection**: scores the *sequence* of coercion
  stages (impersonation → accusation → isolation → secrecy → threat → payment),
  not isolated keywords. Sequence bonuses, repetition dampening, speaker-aware
  scoring and awareness-message guards are all novel relative to keyword filters
  — and the evaluation script quantifies the gap against exactly that baseline.
- Progressive risk timeline turns an invisible manipulation arc into something a
  frightened victim (or a judge) can see message by message.
- Entity reputation + fraud graph makes every complaint improve the next
  detection — a network effect for defence.

## Business impact
- Interrupts fraud **before payment** — the dashboard reports "detected before
  payment request" as a first-class metric, because prevention (not post-hoc
  complaint filing) is where the money is saved.
- Two revenue-relevant surfaces from one engine: a citizen shield (bank app /
  1930-helpline integration) and an investigator command centre (bank fraud
  ops, cyber cells) with mule-endpoint ranking.
- Hindi + English at MVP covers the majority of targeted victims; the rule
  format extends to other Indian languages without re-architecture.

## Technical excellence
- Explainable-by-construction engine: every score point persists as a
  `RiskEvent`; assessments carry engine version, confidence, missing evidence
  and false-positive cautions.
- 27 backend tests (engine units + full API integration), evaluation framework
  with baseline comparison, seeded reproducible demo, Docker Compose, and the
  whole demo runs with **zero external API keys**.
- Auditable evidence: SHA-256 file hashing, append-only audit log, consent
  tracking, PDF reports with disclaimers.

## Scalability
- Engine is stateless per conversation and O(messages × rules) — trivially
  horizontal. SQLite→PostgreSQL is a connection-string change.
- Fraud graph persists as nodes/edges in the relational store and is analysed
  with NetworkX; the same schema maps 1:1 onto Neo4j when complaint volume
  demands it.
- Rule packs are data, deployable server-side without client updates.

## User experience
- Citizen flow is mobile-first and three taps deep: paste/play → watch risk →
  Safety Mode tells you exactly what to do, in your language.
- Safety Mode is designed for panic: huge STOP, imperative steps, helpline 1930,
  no jargon.
- Investigator UI is information-dense where it should be: queue, watchlist,
  graph, hotspots, audit — with "suspected/reported" language enforced.
- Loading skeletons, empty states, error states, toasts and confirmation
  dialogs throughout; severity colours meet contrast on dark navy.
