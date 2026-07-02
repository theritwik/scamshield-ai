# Seed data

The authoritative synthetic seed data (5 scripted demo cases, 15 additional
complaints, and the reported-entity registry) lives in `scripts/seed_data.py`
so it can be loaded idempotently and reset with `--reset`.

Everything is fictional: phone numbers, UPI IDs, bank accounts, URLs and
transcripts are fabricated for the demo. No real victims or personal data.

Load: `python scripts/seed_data.py`
Reset: `python scripts/seed_data.py --reset`
