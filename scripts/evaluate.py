"""Evaluation framework: keyword-only baseline vs the sequence-aware hybrid engine.

Runs both detectors over the synthetic labelled dataset and reports precision,
recall, F1, false-positive rate, confusion matrix, average detection point and
detection-before-payment rate, plus processing latency.

Usage:  python scripts/evaluate.py
Writes: data/evaluation/results.json and data/evaluation/results.md
"""
import json
import re
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.engine.risk_engine import analyse_conversation  # noqa: E402

DATASET = ROOT / "data" / "evaluation" / "labelled_conversations.json"
OUT_JSON = ROOT / "data" / "evaluation" / "results.json"
OUT_MD = ROOT / "data" / "evaluation" / "results.md"

DECISION_THRESHOLD = 50.0  # High/Critical => flag as scam

# --- Baseline: naive keyword matcher (what most simple tools do) ---------------
KEYWORDS = [
    "cbi", "police", "arrest", "digital arrest", "otp", "kyc", "blocked",
    "transfer", "upi", "verification", "customs", "parcel", "money laundering",
    "anydesk", "teamviewer", "urgent", "immediately", "safe account",
    "सीबीआई", "पुलिस", "गिरफ्तार", "ओटीपी", "ट्रांसफर", "पार्सल",
]
KEYWORD_WEIGHT = 18  # each distinct keyword found


def keyword_score(messages: list[dict]) -> float:
    text = " ".join(m["text"].lower() for m in messages)
    found = {k for k in KEYWORDS if k in text}
    return min(100.0, len(found) * KEYWORD_WEIGHT)


def payment_message_index(messages: list[dict]) -> int | None:
    """First message that contains the payment/OTP payload, per simple patterns."""
    payload = re.compile(
        r"(transfer|pay|deposit|send|remit|otp|anydesk|teamviewer|scan|भेज|ट्रांसफर|भुगतान|ओटीपी)",
        re.IGNORECASE,
    )
    for i, m in enumerate(messages):
        if payload.search(m["text"]):
            return i
    return None


def evaluate_engine(conversations: list[dict], detector: str) -> dict:
    tp = fp = tn = fn = 0
    detection_points = []
    before_payment = 0
    payment_scams = 0
    latencies = []
    misclassified = []

    for conv in conversations:
        start = time.perf_counter()
        if detector == "hybrid":
            analyses, result = analyse_conversation(conv["messages"])
            score = result["score"]
            # First message where cumulative risk crossed the threshold.
            detect_idx = next(
                (a.seq for a in analyses if a.cumulative_risk >= DECISION_THRESHOLD), None
            )
        else:
            score = keyword_score(conv["messages"])
            detect_idx = None
            running = set()
            for i, m in enumerate(conv["messages"]):
                low = m["text"].lower()
                running |= {k for k in KEYWORDS if k in low}
                if min(100.0, len(running) * KEYWORD_WEIGHT) >= DECISION_THRESHOLD:
                    detect_idx = i
                    break
        latencies.append((time.perf_counter() - start) * 1000)

        predicted = 1 if score >= DECISION_THRESHOLD else 0
        actual = conv["label"]
        if predicted and actual:
            tp += 1
        elif predicted and not actual:
            fp += 1
            misclassified.append({"id": conv["id"], "type": "false_positive", "score": score})
        elif not predicted and actual:
            fn += 1
            misclassified.append({"id": conv["id"], "type": "false_negative", "score": score})
        else:
            tn += 1

        if actual:
            if detect_idx is not None:
                detection_points.append(detect_idx + 1)
            pay_idx = payment_message_index(conv["messages"])
            if pay_idx is not None:
                payment_scams += 1
                if detect_idx is not None and detect_idx <= pay_idx:
                    before_payment += 1

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0

    return {
        "detector": detector,
        "threshold": DECISION_THRESHOLD,
        "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "false_positive_rate": round(fpr, 3),
        "avg_detection_message": round(statistics.mean(detection_points), 2) if detection_points else None,
        "detected_before_payment_pct": round(before_payment / payment_scams * 100, 1) if payment_scams else None,
        "avg_latency_ms": round(statistics.mean(latencies), 2),
        "misclassified": misclassified,
    }


def main() -> None:
    data = json.loads(DATASET.read_text(encoding="utf-8"))
    conversations = data["conversations"]
    scams = sum(c["label"] for c in conversations)

    baseline = evaluate_engine(conversations, "keyword_baseline")
    hybrid = evaluate_engine(conversations, "hybrid")

    results = {
        "dataset": {
            "path": str(DATASET.relative_to(ROOT)),
            "conversations": len(conversations),
            "scam": scams,
            "legitimate": len(conversations) - scams,
            "note": "Entirely synthetic data; no real victims or identifiers.",
        },
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "results": {"keyword_baseline": baseline, "hybrid_sequence_engine": hybrid},
    }
    OUT_JSON.write_text(json.dumps(results, indent=2), encoding="utf-8")

    def block(r):
        cm = r["confusion_matrix"]
        return (
            f"| Precision | {r['precision']} |\n"
            f"| Recall | {r['recall']} |\n"
            f"| F1 | {r['f1']} |\n"
            f"| False-positive rate | {r['false_positive_rate']} |\n"
            f"| Confusion matrix (TP/FP/TN/FN) | {cm['tp']}/{cm['fp']}/{cm['tn']}/{cm['fn']} |\n"
            f"| Avg detection message | {r['avg_detection_message']} |\n"
            f"| Detected before payment | {r['detected_before_payment_pct']}% |\n"
            f"| Avg latency | {r['avg_latency_ms']} ms |\n"
        )

    md = (
        "# ScamShield AI — Evaluation Report\n\n"
        f"Generated: {results['generated_at']}  \n"
        f"Dataset: {len(conversations)} synthetic conversations "
        f"({scams} scam / {len(conversations) - scams} legitimate), threshold = {DECISION_THRESHOLD}.\n\n"
        "## Keyword-only baseline\n\n| Metric | Value |\n|---|---|\n" + block(baseline) +
        "\n## Hybrid sequence-aware engine\n\n| Metric | Value |\n|---|---|\n" + block(hybrid) +
        "\n## Misclassifications (hybrid)\n\n" +
        ("\n".join(f"- `{m['id']}` — {m['type']} (score {m['score']})" for m in hybrid["misclassified"]) or "None.") +
        "\n\n## Misclassifications (baseline)\n\n" +
        ("\n".join(f"- `{m['id']}` — {m['type']} (score {m['score']})" for m in baseline["misclassified"]) or "None.") +
        "\n\n*All figures are produced by `scripts/evaluate.py` on synthetic data and will vary as rules evolve. "
        "They are not claims about real-world performance.*\n"
    )
    OUT_MD.write_text(md, encoding="utf-8")

    print(json.dumps({k: {m: v for m, v in r.items() if m != "misclassified"}
                      for k, r in results["results"].items()}, indent=2))
    print(f"\nWrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
