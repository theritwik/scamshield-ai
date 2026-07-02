# Threat model (prototype scope)

## Assets
- Victim conversation content (potentially sensitive personal data)
- Extracted identifiers (phones, UPI IDs, bank accounts)
- Evidence files and their integrity hashes
- Audit trail integrity
- Investigator dashboard data

## Trust boundaries
1. Citizen browser ↔ FastAPI (public, unauthenticated in prototype)
2. Investigator browser ↔ FastAPI (demo-token gated)
3. FastAPI ↔ optional external transcription provider (outbound only, opt-in)

## Mitigations implemented
| Threat | Mitigation |
|---|---|
| Malicious file upload | Content-type allowlist (png/jpg/mp3/wav/txt), 8 MB cap, random stored filenames, no execution, original filename truncated |
| Path traversal | Uploads stored under a server-chosen UUID name; stored paths never accepted from clients; report downloads resolved by DB id only |
| Malicious QR/UPI payloads | Decoded and displayed only; never opened, executed or auto-paid |
| Phishing URLs in evidence | Rendered as text, never as clickable links in reports |
| PII exposure | Masking at extraction time; masked values used in UI and PDF; reveal only behind investigator demo token, synthetic data only |
| Injection via message text | SQLAlchemy parameterised queries; Pydantic validation with length caps; React auto-escaping; PDF text escaped before ReportLab markup |
| Audit tampering | Append-only service; no delete/update endpoint exists |
| Secrets leakage | All secrets via environment variables; no keys in frontend bundle; `.env` gitignored; mock adapters used when keys absent |
| CORS abuse | Explicit origin allowlist |
| Oversized/DoS input | Message length (4000), bulk cap (200), case list cap, upload cap |

## Accepted risks (prototype, documented)
- **No real authentication**: the investigator token is a static demo credential;
  any deployment beyond a demo requires SSO/OIDC, per-user roles and audit of reads.
- **No rate limiting**: acceptable for a local demo; add a reverse-proxy limiter in production.
- **SQLite durability**: single-writer demo store; PostgreSQL for anything real.
- **Rule evasion**: adversaries who know the rules can rephrase; the roadmap counters
  with semantic similarity and continuously updated script clusters.
- **Mock media adapters**: outputs are clearly labelled `provider: mock` and must
  never be treated as real transcriptions/decodes in evaluations.

## Abuse cases considered
- A malicious user uploading someone else's private conversation → consent
  checkbox recorded per case; reports carry consent status; retention should be
  minimal (see privacy.md).
- Using the tool to "pre-test" scam scripts → the engine and weights are public
  in the repo anyway for the hackathon; production deployment would keep rule
  updates server-side and monitored.
