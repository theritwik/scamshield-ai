# ScamShield AI — Evaluation Report

Generated: 2026-07-02T13:06:03Z  
Dataset: 24 synthetic conversations (13 scam / 11 legitimate), threshold = 50.0.

## Keyword-only baseline

| Metric | Value |
|---|---|
| Precision | 0.889 |
| Recall | 0.615 |
| F1 | 0.727 |
| False-positive rate | 0.091 |
| Confusion matrix (TP/FP/TN/FN) | 8/1/10/5 |
| Avg detection message | 2.88 |
| Detected before payment | 50.0% |
| Avg latency | 0.01 ms |

## Hybrid sequence-aware engine

| Metric | Value |
|---|---|
| Precision | 1.0 |
| Recall | 0.923 |
| F1 | 0.96 |
| False-positive rate | 0.0 |
| Confusion matrix (TP/FP/TN/FN) | 12/0/11/1 |
| Avg detection message | 3.17 |
| Detected before payment | 58.3% |
| Avg latency | 0.34 ms |

## Misclassifications (hybrid)

- `scam-kyc-01` — false_negative (score 40.0)

## Misclassifications (baseline)

- `scam-kyc-02` — false_negative (score 18)
- `scam-remote-01` — false_negative (score 36)
- `scam-upi-01` — false_negative (score 18)
- `scam-da-07` — false_negative (score 36)
- `scam-otp-01` — false_negative (score 18)
- `legit-friend-01` — false_positive (score 72)

*All figures are produced by `scripts/evaluate.py` on synthetic data and will vary as rules evolve. They are not claims about real-world performance.*
