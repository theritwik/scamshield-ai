"""Seed the ScamShield AI database with entirely fictional, synthetic demo data.

Creates the 5 scripted demo cases plus 15 additional synthetic complaints,
a reported-entity registry, and a visible fraud ring (shared UPI/phone across
complaints in multiple cities). Every identifier is fabricated.

Usage:  python scripts/seed_data.py [--reset]
"""
import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "api"))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Case, ConversationMessage, ReportedEntity  # noqa: E402
from app.services import audit  # noqa: E402
from app.services.analysis import analyse_case  # noqa: E402

random.seed(42)

CITIES = ["Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Lucknow"]

# --- Fictional reported entities (the synthetic fraud registry) ---------------
REPORTED = [
    ("phone", "9812345670", 4, "CBI impersonation ring"),
    ("phone", "9765432180", 3, "CBI impersonation ring"),
    ("phone", "8899776650", 2, "KYC phishing"),
    ("upi_id", "rbi.verify@ybl", 4, "safe-account mule"),
    ("upi_id", "cbi.clearance@ptyes", 3, "safe-account mule"),
    ("upi_id", "kyc.update@okicici", 2, "KYC phishing"),
    ("bank_account", "912345678901", 3, "mule account"),
    ("url", "http://kyc-sbi-update.example-fraud.in", 2, "phishing site"),
]

# --- The five scripted demo cases ---------------------------------------------
RING_PHONE = "9812345670"
RING_UPI = "rbi.verify@ybl"
RING_UPI2 = "cbi.clearance@ptyes"
RING_ACC = "912345678901"

DEMO_CASES = [
    {
        "title": "CASE 1 — Critical digital-arrest scam (CBI impersonation)",
        "language": "en",
        "source_type": "call",
        "city": "Mumbai",
        "messages": [
            ("caller", "Hello, I am calling from TRAI. Your Aadhaar has been linked to an illegal parcel intercepted by Customs."),
            ("victim", "What parcel? I never sent anything."),
            ("caller", f"This is serious. I am transferring your call to a CBI officer. Note this case number and call {RING_PHONE} if disconnected."),
            ("caller", "This is Inspector Rathi, CBI Mumbai. A case of money laundering has been registered against you."),
            ("caller", "This is a confidential national security matter. Do not tell your family or anyone about this investigation."),
            ("caller", "Go to a separate room and stay alone. Do not disconnect this video call. You are under digital arrest."),
            ("victim", "Please, I am a retired teacher. I have done nothing wrong."),
            ("caller", "If you want to avoid arrest tonight, you must act immediately."),
            ("caller", f"Transfer ₹50,000 to the safe RBI verification account. Pay to {RING_UPI} right now. The money will be returned after verification."),
        ],
    },
    {
        "title": "CASE 2 — Suspicious bank KYC message with malicious link",
        "language": "en",
        "source_type": "sms",
        "city": "Delhi",
        "messages": [
            ("caller", "Dear customer, your account will be blocked in 2 hours. Complete KYC immediately: http://kyc-sbi-update.example-fraud.in"),
        ],
    },
    {
        "title": "CASE 3 — Legitimate bank awareness message (low risk)",
        "language": "en",
        "source_type": "sms",
        "city": "Bengaluru",
        "messages": [
            ("caller", "Dear customer, your bank will never ask for your OTP, PIN or CVV. Never share banking details with anyone. Beware of fraudsters asking you to install remote apps. Report suspicious calls to 1930. Stay safe."),
        ],
    },
    {
        "title": "CASE 4 — Hindi police impersonation scam (डिजिटल अरेस्ट)",
        "language": "hi",
        "source_type": "call",
        "city": "Lucknow",
        "messages": [
            ("caller", "मैं दिल्ली पुलिस साइबर सेल से इंस्पेक्टर बोल रहा हूं। आपके आधार से एक अवैध पार्सल जुड़ा है।"),
            ("victim", "मुझे कुछ नहीं पता, कोई गलती हुई है।"),
            ("caller", "आपके खिलाफ मनी लॉन्ड्रिंग का केस दर्ज है। गिरफ्तारी का वारंट जारी हो चुका है।"),
            ("caller", "यह गुप्त जांच है। परिवार में किसी को मत बताना। अलग कमरे में जाइए।"),
            ("caller", "वीडियो कॉल मत काटिए। आप डिजिटल अरेस्ट में हैं।"),
            ("caller", f"बचना है तो तुरंत 2 लाख रुपये ट्रांसफर करें। {RING_UPI2} पर भुगतान करें।"),
        ],
    },
    {
        "title": "CASE 5 — Remote-access 'support' scam (OTP + screen share)",
        "language": "en",
        "source_type": "call",
        "city": "Hyderabad",
        "messages": [
            ("caller", "Hello, I am calling from your bank's security department. Suspicious activity was detected on your card."),
            ("caller", "To secure your account, install AnyDesk from the Play Store and share your screen with me."),
            ("victim", "Is this really necessary?"),
            ("caller", "Yes, do it immediately or your account will be frozen today."),
            ("caller", "Now tell me the OTP you just received so I can verify your identity."),
        ],
    },
]

# --- Additional synthetic complaints to populate the graph and dashboard -------
EXTRA_TEMPLATES = [
    # The fraud ring: same UPI / phone across cities with similar scripts.
    ("call", "en", "Digital arrest call — parcel + CBI script",
     [("caller", "I am from Customs, an illegal parcel with your Aadhaar was seized."),
      ("caller", "CBI officer will speak to you now. A money laundering case is registered against you."),
      ("caller", "Do not tell anyone, this is confidential. Stay on the video call."),
      ("caller", f"Transfer the verification amount to the safe account, pay to {RING_UPI} immediately.")]),
    ("call", "en", "Digital arrest call — courier + police script",
     [("caller", f"This is Delhi Police. Your parcel contains illegal items. Call {RING_PHONE} for the investigating officer."),
      ("caller", "You will be arrested unless you cooperate. Do not inform your family."),
      ("caller", f"Deposit ₹80,000 to account {RING_ACC} for verification. It will be refunded.")]),
    ("call", "hi", "डिजिटल अरेस्ट कॉल — सीबीआई स्क्रिप्ट",
     [("caller", "मैं सीबीआई अधिकारी बोल रहा हूं। आपके नाम से अवैध पार्सल पकड़ा गया है।"),
      ("caller", "किसी को मत बताइए। वीडियो कॉल पर बने रहिए।"),
      ("caller", f"तुरंत {RING_UPI} पर 50000 रुपये भेजिए, जांच के बाद वापस मिलेंगे।")]),
    ("sms", "en", "KYC phishing SMS",
     [("caller", "Your account will be suspended today. Update KYC now: http://kyc-sbi-update.example-fraud.in or call 8899776650.")]),
    ("call", "en", "Remote access scam — TeamViewer",
     [("caller", "Sir, your electricity bill is unpaid, your power will be cut tonight."),
      ("caller", "Download TeamViewer QuickSupport and give me the access code immediately."),
      ("caller", "Now share the OTP to stop the disconnection.")]),
]


def seed(reset: bool = False) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if reset:
            # Demo reset: wipes all data and recreates the synthetic environment.
            for table in reversed(Base.metadata.sorted_tables):
                db.execute(table.delete())
            db.commit()
            print("Database reset.")

        if db.query(Case).filter(Case.is_demo_seed.is_(True)).count():
            print("Seed data already present. Use --reset to reseed.")
            return

        for etype, norm, count, note in REPORTED:
            db.add(ReportedEntity(entity_type=etype, normalized=norm, report_count=count, note=note))
        db.commit()

        def create_case(title, language, source_type, city, messages):
            case = Case(
                case_number=f"SSA-2026-{db.query(Case).count() + 1:05d}",
                title=title, language=language, source_type=source_type,
                consent_given=True, city=city, is_demo_seed=True,
            )
            db.add(case)
            db.flush()
            audit.record(db, "citizen", "case_created", case.id, meta={"seed": True})
            for i, (speaker, text) in enumerate(messages):
                db.add(ConversationMessage(
                    case_id=case.id, seq=i, speaker=speaker, text=text, language=language,
                ))
            db.flush()
            db.refresh(case)
            analyse_case(db, case, actor="seed-script")
            db.commit()
            return case

        for spec in DEMO_CASES:
            c = create_case(spec["title"], spec["language"], spec["source_type"], spec["city"], spec["messages"])
            print(f"  {c.case_number}  {c.severity:<8}  {c.final_risk_score:>5.1f}  {c.title[:60]}")

        for i in range(15):
            src, lang, title, msgs = EXTRA_TEMPLATES[i % len(EXTRA_TEMPLATES)]
            city = CITIES[i % len(CITIES)]
            c = create_case(f"{title} #{i + 1}", lang, src, city, msgs)
            print(f"  {c.case_number}  {c.severity:<8}  {c.final_risk_score:>5.1f}  {c.title[:60]}")

        print("Seeded 20 synthetic complaints (all fictional data).")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="wipe and reseed the demo database")
    args = parser.parse_args()
    seed(reset=args.reset)
