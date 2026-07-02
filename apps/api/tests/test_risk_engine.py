"""Unit tests for the sequence-aware risk engine."""
from app.engine.risk_engine import (
    ConversationState,
    analyse_conversation,
    analyse_message,
    normalise,
    severity_for,
)

DIGITAL_ARREST = [
    {"speaker": "caller", "text": "Hello, I am calling from Mumbai Police cyber cell."},
    {"speaker": "caller", "text": "Your Aadhaar has been linked to an illegal parcel containing drugs."},
    {"speaker": "caller", "text": "I am transferring your call to a senior CBI officer."},
    {"speaker": "caller", "text": "A case of money laundering has been registered against you."},
    {"speaker": "caller", "text": "Do not tell your family about this investigation. Go to a separate room."},
    {"speaker": "caller", "text": "This is a confidential matter of national security. Do not disclose this call."},
    {"speaker": "caller", "text": "Do not disconnect this video call. You are under digital arrest."},
    {"speaker": "caller", "text": "You must act immediately or you will be arrested tonight."},
    {"speaker": "caller", "text": "Transfer Rs 50,000 to the safe RBI verification account right now."},
]

LEGIT_BANK_AWARENESS = [
    {
        "speaker": "caller",
        "text": "Dear customer, SBI never asks for your OTP, PIN or CVV. "
        "Never share banking details with anyone. Beware of fraudsters. Stay safe.",
    }
]

CASUAL = [
    {"speaker": "caller", "text": "Hi, are we still meeting for lunch tomorrow at 1pm?"},
    {"speaker": "victim", "text": "Yes, see you at the usual place."},
]


def test_digital_arrest_reaches_critical():
    analyses, result = analyse_conversation(DIGITAL_ARREST)
    assert result["severity"] == "Critical"
    assert result["score"] >= 75
    assert result["category"] == "digital_arrest_scam"


def test_risk_is_progressive_and_monotonic():
    analyses, _ = analyse_conversation(DIGITAL_ARREST)
    risks = [a.cumulative_risk for a in analyses]
    assert risks == sorted(risks)
    assert risks[0] < 30  # a greeting + authority claim alone is not critical
    assert risks[-1] >= 75


def test_sequence_bonus_awarded():
    _, result = analyse_conversation(DIGITAL_ARREST)
    kinds = [r["kind"] for r in result["top_reasons"]]
    assert "sequence_bonus" in kinds


def test_stage_order_recorded():
    analyses, result = analyse_conversation(DIGITAL_ARREST)
    stages = [s["stage"] for s in result["stages_detected"]]
    assert stages.index("authority_impersonation") < stages.index("payment_or_access_request")
    assert "isolation" in stages and "threat" in stages


def test_awareness_message_scores_low():
    _, result = analyse_conversation(LEGIT_BANK_AWARENESS)
    assert result["severity"] == "Low"
    assert result["score"] < 25


def test_casual_conversation_scores_zero_ish():
    _, result = analyse_conversation(CASUAL)
    assert result["score"] < 10
    assert result["category"] == "no_scam_indicators"


def test_repetition_dampening():
    state = ConversationState()
    first = analyse_message(state, 0, "caller", "You will be arrested tonight.")
    second = analyse_message(state, 1, "caller", "You will be arrested, I repeat, arrested.")
    w_first = sum(h.weight for h in first.hits)
    w_second = sum(h.weight for h in second.hits)
    assert w_second < w_first


def test_victim_speech_not_scored_as_coercion():
    state = ConversationState()
    analysis = analyse_message(
        state, 0, "victim", "He said I would be arrested and asked me to transfer money."
    )
    assert not [h for h in analysis.hits if h.kind == "signal"]


def test_single_keyword_not_critical():
    _, result = analyse_conversation(
        [{"speaker": "caller", "text": "Please transfer Rs 500 for the lunch bill."}]
    )
    assert result["severity"] in ("Low", "Medium")
    assert result["confidence"] <= 0.55


def test_reported_entity_boost():
    _, no_rep = analyse_conversation(
        [{"speaker": "caller", "text": "Pay to verify@ybl now, transfer Rs 9000."}]
    )
    _, with_rep = analyse_conversation(
        [{"speaker": "caller", "text": "Pay to verify@ybl now, transfer Rs 9000."}],
        reported_lookup=lambda text: {"verify@ybl"} if "verify@ybl" in text else set(),
    )
    assert with_rep["score"] > no_rep["score"]


def test_hindi_digital_arrest_detected():
    hindi = [
        {"speaker": "caller", "text": "मैं सीबीआई अधिकारी बोल रहा हूं।"},
        {"speaker": "caller", "text": "आपके नाम से एक अवैध पार्सल पकड़ा गया है।"},
        {"speaker": "caller", "text": "किसी को मत बताना, यह गुप्त जांच है।"},
        {"speaker": "caller", "text": "वीडियो कॉल मत काटिए, आप डिजिटल अरेस्ट में हैं।"},
        {"speaker": "caller", "text": "तुरंत 50000 रुपये सेफ अकाउंट में ट्रांसफर करें।"},
    ]
    _, result = analyse_conversation(hindi)
    assert result["severity"] in ("High", "Critical")
    assert result["score"] >= 60


def test_normalise_bounds_and_severity():
    assert normalise(-5) == 0.0
    assert normalise(10_000) == 100.0
    assert severity_for(0) == "Low"
    assert severity_for(25) == "Medium"
    assert severity_for(50) == "High"
    assert severity_for(75) == "Critical"
