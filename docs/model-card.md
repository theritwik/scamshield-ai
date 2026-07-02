# Model card — ScamShield AI coercion-detection engine

**Version:** scamshield-risk-engine/1.0.0
**Type:** Deterministic hybrid rule engine (weighted signals + sequence logic + entity reputation). No neural model makes decisions in the MVP.

## Intended use
- Decision support for citizens assessing whether an ongoing interaction shows
  digital-arrest / payment-fraud coercion patterns (English and Hindi).
- Triage support for bank/law-enforcement analysts reviewing complaints.
- Education: the explanations teach users what coercion stages look like.

## Out-of-scope use
- Automated blocking of payments, accounts, calls or people.
- Legal determination of fraud, guilt or criminal liability.
- Live telecom interception or surveillance of any kind.
- Real-time voice/deepfake detection (not implemented).
- Deployment against real complaint data without a privacy/legal review.

## Data sources
- Signal patterns were authored from publicly reported digital-arrest scam
  scripts (news reports, police advisories, RBI/cybercrime awareness material).
- Evaluation and seed data are **entirely synthetic** and written for this
  project (`data/evaluation/labelled_conversations.json`, `scripts/seed_data.py`).
- No real victim data was used anywhere.

## Evaluation
Run `python scripts/evaluate.py`. All published numbers come from that script's
output (`data/evaluation/results.json` / `.md`) on the synthetic dataset; the
README intentionally cites no accuracy figures that the script did not produce.
The evaluation compares a keyword-count baseline against the sequence-aware
engine on precision, recall, F1, false-positive rate, average detection message
and detection-before-payment rate.

## Known limitations
- **Synthetic evaluation**: results measure behaviour on scripted patterns, not
  real-world performance; real transcripts are noisier and adversarial.
- **Rule brittleness**: novel phrasings or code-switching (Hinglish in Latin
  script) may be missed; romanised Hindi coverage is partial.
- **Short-input uncertainty**: single messages cap confidence at 0.55 and often
  land in Medium — deliberately, to control false positives.
- **ASR/OCR dependence**: garbled transcription or OCR degrades detection; mock
  adapters are for demo only.

## False-positive risks
Legitimate urgent communication (genuine bank fraud alerts, real authority
contact, debt-collection notices) shares vocabulary with scams. Controls:
awareness-message guards, sequence requirements, repetition dampening,
speaker-aware scoring, confidence scores, and an explicit
`false_positive_caution` string attached to every assessment.

## Human review requirements
Every assessment is labelled decision-support. The investigator workflow
(review decisions, append-only audit, "suspected/reported" language) exists so
that **no adverse action is taken from the score alone**. Graph insights never
assert guilt and always state that human verification is required.
