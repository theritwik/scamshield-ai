# Privacy

## Principles
1. **Consent first** — a case cannot be created without the consent checkbox;
   consent status is stored on the case and printed in every evidence report.
2. **Mask by default** — phones, UPI IDs, accounts, emails, URLs and officer
   names are masked at extraction time (`XXXXXX4821`, `+91-98XXXXXX52`).
   The public UI and PDF reports only ever show masked values. The investigator
   demo token may reveal *seeded synthetic* identifiers only.
3. **Minimal retention** — uploads are stored under random names solely to
   preserve evidence integrity; the demo database can be wiped and reseeded at
   any time (`python scripts/seed_data.py --reset`). A production deployment
   would add automatic raw-evidence expiry.
4. **Integrity over collection** — SHA-256 hashes of every upload are stored so
   evidence can be verified later without re-sharing the file.
5. **No raw evidence in logs** — message text and file contents are never
   written to server logs; audit metadata carries hashes and counts, not content.
6. **No third-party sharing** — the demo makes no external calls unless an
   optional transcription key is explicitly configured; "alerts" to banks,
   police and contacts are simulated and labelled as such.
7. **Synthetic data only** — every seeded complaint, number, account and
   transcript is fictional.

## Data subject considerations (for a real deployment)
- Lawful basis and DPDP Act 2023 compliance review before any real data.
- Right-to-erasure workflow that preserves audit integrity (tombstoning).
- Separate encrypted storage for raw evidence with strict TTL.
- Access logging for investigator reads (partially present via audit trail).
