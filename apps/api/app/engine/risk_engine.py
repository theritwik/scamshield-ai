"""Sequence-aware, explainable risk engine.

The engine consumes a conversation message by message and produces:
  - per-message detected signals with weights and matched excerpts,
  - sequence bonuses when coercion stages occur in a scam-typical order,
  - entity-reputation boosts for previously reported entities,
  - a cumulative 0-100 score with severity, confidence and reasons.

No LLM is involved in the decision. Every point of the score traces back to a
named rule, sequence bonus or reputation record, which is what makes the
result auditable.
"""
from dataclasses import dataclass, field

from .signals import (
    COMPILED,
    COMPILED_GUARDS,
    SEQUENCE_BONUSES,
    SIGNALS_BY_ID,
    STAGE_LABELS,
)

# Repeating the same signal keeps reinforcing risk, but with diminishing returns
# so a keyword repeated ten times cannot alone saturate the score.
REPEAT_DECAY = 0.4
# Raw weighted sum that maps to score 100. Chosen so that a full coercion
# sequence (5-6 stages plus bonuses) lands in the Critical band while one or
# two isolated signals stay Low/Medium.
NORMALISATION_CEILING = 130.0

SEVERITY_BANDS = (
    (75, "Critical"),
    (50, "High"),
    (25, "Medium"),
    (0, "Low"),
)


@dataclass
class SignalHit:
    signal_id: str
    stage: str
    label: str
    label_hi: str
    weight: float
    matched_text: str
    explanation: str
    explanation_hi: str
    kind: str = "signal"  # signal | sequence_bonus | entity_reputation


@dataclass
class MessageAnalysis:
    seq: int
    speaker: str
    text: str
    hits: list[SignalHit] = field(default_factory=list)
    risk_delta: float = 0.0
    cumulative_risk: float = 0.0
    stages: list[str] = field(default_factory=list)


@dataclass
class ConversationState:
    """Carries the engine state across messages of one case."""

    raw_score: float = 0.0
    signal_counts: dict[str, int] = field(default_factory=dict)
    stage_order: list[str] = field(default_factory=list)  # stages in first-seen order
    awarded_bonuses: set[tuple[str, str]] = field(default_factory=set)
    reported_entity_hits: set[str] = field(default_factory=set)


def severity_for(score: float) -> str:
    for threshold, name in SEVERITY_BANDS:
        if score >= threshold:
            return name
    return "Low"


def normalise(raw: float) -> float:
    return round(min(100.0, max(0.0, raw / NORMALISATION_CEILING * 100.0)), 1)


def _match_signals(text: str) -> list[SignalHit]:
    hits: list[SignalHit] = []
    for signal_id, regexes in COMPILED.items():
        signal = SIGNALS_BY_ID[signal_id]
        match = None
        for rx in regexes:
            match = rx.search(text)
            if match:
                break
        if not match:
            continue
        # Awareness guard: skip if the message is educating rather than coercing.
        if any(g.search(text) for g in COMPILED_GUARDS[signal_id]):
            continue
        hits.append(
            SignalHit(
                signal_id=signal.id,
                stage=signal.stage,
                label=signal.label,
                label_hi=signal.label_hi,
                weight=signal.weight,
                matched_text=match.group(0)[:160],
                explanation=signal.explanation,
                explanation_hi=signal.explanation_hi,
            )
        )
    return hits


def analyse_message(
    state: ConversationState,
    seq: int,
    speaker: str,
    text: str,
    reported_entities: set[str] | None = None,
) -> MessageAnalysis:
    """Analyse one message, mutate state, return the per-message analysis.

    ``reported_entities`` is the set of normalised entity values found in this
    message that already exist in the reported-entity registry.
    """
    analysis = MessageAnalysis(seq=seq, speaker=speaker, text=text)
    # Victim/user messages provide context but only the counterpart's messages
    # carry coercion weight; a victim quoting the scammer should not self-inflate.
    coercive_speaker = speaker.lower() not in ("victim", "user", "citizen", "me")

    delta = 0.0
    if coercive_speaker:
        for hit in _match_signals(text):
            count = state.signal_counts.get(hit.signal_id, 0)
            effective = hit.weight * (REPEAT_DECAY**count)
            hit.weight = round(effective, 2)
            state.signal_counts[hit.signal_id] = count + 1
            if hit.stage not in state.stage_order:
                state.stage_order.append(hit.stage)
            analysis.hits.append(hit)
            delta += effective

        # Sequence bonuses: award once when the later stage appears after the
        # earlier stage in first-seen order.
        seen = state.stage_order
        for earlier, later, bonus, why in SEQUENCE_BONUSES:
            key = (earlier, later)
            if key in state.awarded_bonuses:
                continue
            if earlier in seen and later in seen and seen.index(earlier) < seen.index(later):
                if later in [h.stage for h in analysis.hits]:
                    state.awarded_bonuses.add(key)
                    analysis.hits.append(
                        SignalHit(
                            signal_id=f"seq:{earlier}->{later}",
                            stage=later,
                            label=f"Sequence: {STAGE_LABELS[earlier][0]} → {STAGE_LABELS[later][0]}",
                            label_hi=f"क्रम: {STAGE_LABELS[earlier][1]} → {STAGE_LABELS[later][1]}",
                            weight=bonus,
                            matched_text="",
                            explanation=why,
                            explanation_hi=why,
                            kind="sequence_bonus",
                        )
                    )
                    delta += bonus

    # Entity reputation applies regardless of speaker: a victim pasting a UPI ID
    # that is already in four complaints is a strong signal.
    for ent in sorted(reported_entities or set()):
        if ent in state.reported_entity_hits:
            continue
        state.reported_entity_hits.add(ent)
        analysis.hits.append(
            SignalHit(
                signal_id=f"reputation:{ent}",
                stage="payment_or_access_request",
                label="Previously reported entity",
                label_hi="पहले से रिपोर्ट की गई पहचान",
                weight=15,
                matched_text=ent,
                explanation="This identifier already appears in earlier complaints in the (synthetic) fraud registry.",
                explanation_hi="यह पहचान पहले की शिकायतों में दर्ज है (सिंथेटिक रजिस्ट्री)।",
                kind="entity_reputation",
            )
        )
        delta += 15

    prev_score = normalise(state.raw_score)
    state.raw_score += delta
    new_score = normalise(state.raw_score)
    analysis.risk_delta = round(new_score - prev_score, 1)
    analysis.cumulative_risk = new_score
    analysis.stages = sorted({h.stage for h in analysis.hits if h.kind == "signal"})
    return analysis


def confidence_for(state: ConversationState, message_count: int) -> float:
    """Confidence grows with distinct corroborating stages and sequence structure.

    A single keyword in a single message gives low confidence even if weighty;
    multiple stages in scam-typical order give high confidence.
    """
    distinct_stages = len(state.stage_order)
    bonuses = len(state.awarded_bonuses)
    base = min(1.0, 0.18 * distinct_stages + 0.08 * bonuses)
    if message_count < 2:
        base = min(base, 0.55)
    return round(max(0.1, base), 2)


def categorise(state: ConversationState) -> str:
    stages = set(state.stage_order)
    if {"authority_impersonation", "threat"} <= stages or "continuous_call" in stages:
        return "digital_arrest_scam"
    if state.signal_counts.get("link_bait") and "threat" in stages:
        return "kyc_phishing"
    if state.signal_counts.get("remote_access_request"):
        return "remote_access_support_scam"
    if "payment_or_access_request" in stages and "authority_impersonation" in stages:
        return "impersonation_payment_fraud"
    if "payment_or_access_request" in stages:
        return "payment_fraud"
    if stages:
        return "suspicious_social_engineering"
    return "no_scam_indicators"


CATEGORY_LABELS = {
    "digital_arrest_scam": ("Digital-arrest scam", "डिजिटल अरेस्ट धोखाधड़ी"),
    "kyc_phishing": ("KYC / account-blocking phishing", "KYC / खाता ब्लॉक फ़िशिंग"),
    "remote_access_support_scam": ("Remote-access support scam", "रिमोट एक्सेस सपोर्ट धोखाधड़ी"),
    "impersonation_payment_fraud": ("Impersonation payment fraud", "प्रतिरूपण भुगतान धोखाधड़ी"),
    "payment_fraud": ("Payment fraud attempt", "भुगतान धोखाधड़ी का प्रयास"),
    "suspicious_social_engineering": ("Suspicious social engineering", "संदिग्ध सोशल इंजीनियरिंग"),
    "no_scam_indicators": ("No scam indicators found", "धोखाधड़ी के संकेत नहीं मिले"),
}


def summarise(
    state: ConversationState, analyses: list[MessageAnalysis]
) -> dict:
    """Build the final explainable assessment from the accumulated state."""
    score = normalise(state.raw_score)
    severity = severity_for(score)
    all_hits = [h for a in analyses for h in a.hits]
    top = sorted(all_hits, key=lambda h: -h.weight)[:6]
    stages_detected = [
        {
            "stage": s,
            "label": STAGE_LABELS[s][0],
            "label_hi": STAGE_LABELS[s][1],
            "order": i + 1,
        }
        for i, s in enumerate(state.stage_order)
    ]

    recommended, missing = [], []
    if severity in ("Critical", "High"):
        recommended = [
            "Do not transfer money or share OTP/PIN/CVV.",
            "End the call and speak to a trusted family member immediately.",
            "Contact your bank on its official number to secure your accounts.",
            "Report at cybercrime.gov.in or call the 1930 helpline.",
            "Preserve screenshots, recordings and this analysis as evidence.",
        ]
    elif severity == "Medium":
        recommended = [
            "Do not act on the message; verify through official channels.",
            "Do not click links; open your bank's app or website directly.",
            "Add more of the conversation for a fuller analysis.",
        ]
    else:
        recommended = [
            "No coercion pattern found so far. Stay alert for payment or OTP requests.",
            "Re-run the analysis if the conversation continues.",
        ]

    if not state.reported_entity_hits:
        missing.append("No phone/UPI/account identifier supplied — entity reputation could not be checked.")
    if len(analyses) < 3:
        missing.append("Only a short excerpt was analysed; more of the conversation would raise confidence.")
    if "payment_or_access_request" not in state.stage_order:
        missing.append("No payment/OTP demand observed yet — the scam may not have reached its payload stage.")

    fp_caution = (
        "Rule-based signals can fire on legitimate urgent communication (e.g. genuine bank fraud alerts). "
        "This assessment is decision support and requires human judgement; it is not a legal determination."
    )

    return {
        "score": score,
        "severity": severity,
        "confidence": confidence_for(state, len(analyses)),
        "category": categorise(state),
        "category_label": CATEGORY_LABELS[categorise(state)][0],
        "category_label_hi": CATEGORY_LABELS[categorise(state)][1],
        "stages_detected": stages_detected,
        "top_reasons": [
            {
                "label": h.label,
                "label_hi": h.label_hi,
                "weight": h.weight,
                "kind": h.kind,
                "excerpt": h.matched_text,
                "explanation": h.explanation,
                "explanation_hi": h.explanation_hi,
            }
            for h in top
        ],
        "recommended_actions": recommended,
        "missing_evidence": missing,
        "false_positive_caution": fp_caution,
    }


def analyse_conversation(
    messages: list[dict],
    reported_lookup=None,
) -> tuple[list[MessageAnalysis], dict]:
    """Convenience wrapper: analyse a full conversation.

    ``messages``: [{"speaker": ..., "text": ...}, ...]
    ``reported_lookup``: callable(text) -> set of normalised reported entities.
    """
    state = ConversationState()
    analyses = []
    for i, msg in enumerate(messages):
        reported = reported_lookup(msg["text"]) if reported_lookup else set()
        analyses.append(
            analyse_message(state, i, msg.get("speaker", "caller"), msg["text"], reported)
        )
    return analyses, summarise(state, analyses)
