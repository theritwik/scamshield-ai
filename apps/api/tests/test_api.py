"""API integration tests against a temporary SQLite database."""
import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["SCAMSHIELD_UPLOAD_DIR"] = tempfile.mkdtemp()
os.environ["SCAMSHIELD_REPORT_DIR"] = tempfile.mkdtemp()

from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app

Base.metadata.create_all(bind=engine)
client = TestClient(app)

INVESTIGATOR = {"X-Investigator-Token": "demo-investigator"}


def make_case(**overrides):
    payload = {
        "title": "Test digital arrest call",
        "language": "en",
        "source_type": "call",
        "consent_given": True,
        "city": "Mumbai",
    }
    payload.update(overrides)
    r = client.post("/api/cases", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_consent_required():
    r = client.post("/api/cases", json={"title": "x", "consent_given": False})
    assert r.status_code == 422


def test_full_case_flow():
    case = make_case()
    lines = [
        "I am calling from the CBI. Your Aadhaar is linked to an illegal parcel.",
        "A money laundering case has been registered against you.",
        "Do not tell your family. Stay in a separate room. This is confidential.",
        "Do not disconnect this video call. You are under digital arrest.",
        "Transfer Rs 50,000 to the safe RBI verification account 123456784821 immediately.",
    ]
    last = None
    for line in lines:
        r = client.post(f"/api/cases/{case['id']}/messages", json={"speaker": "caller", "text": line})
        assert r.status_code == 200, r.text
        last = r.json()

    assert last["assessment"]["severity"] == "Critical"
    assert last["message"]["cumulative_risk"] >= 75

    # Risk timeline is monotonic.
    r = client.get(f"/api/cases/{case['id']}/risk-timeline")
    risks = [p["cumulative_risk"] for p in r.json()["points"]]
    assert risks == sorted(risks)

    # Entities extracted and masked.
    r = client.get(f"/api/cases/{case['id']}/entities")
    ents = r.json()
    assert any(e["entity_type"] == "bank_account" for e in ents)
    assert all("123456784821" not in e["masked"] for e in ents)

    # PDF report.
    r = client.post(f"/api/cases/{case['id']}/generate-report")
    assert r.status_code == 200
    report = r.json()
    assert len(report["sha256"]) == 64
    r = client.get(report["download"])
    assert r.status_code == 200
    assert r.content[:5] == b"%PDF-"

    # Audit trail recorded, including analysis + report events.
    r = client.get(f"/api/audit/{case['id']}")
    actions = [a["action"] for a in r.json()]
    assert "case_created" in actions
    assert "analysis_performed" in actions
    assert "report_generated" in actions

    # Case graph exists.
    r = client.get(f"/api/cases/{case['id']}/graph")
    g = r.json()
    assert any(n["type"] == "complaint" for n in g["nodes"])


def test_dashboard_requires_token():
    assert client.get("/api/dashboard/summary").status_code == 401
    r = client.get("/api/dashboard/summary", headers=INVESTIGATOR)
    assert r.status_code == 200
    assert r.json()["total_complaints"] >= 1


def test_review_workflow():
    case = make_case(title="Review me")
    client.post(f"/api/cases/{case['id']}/messages", json={"speaker": "caller", "text": "hello"})
    r = client.post(
        f"/api/cases/{case['id']}/review",
        json={"decision": "not_scam", "notes": "benign"},
    )
    assert r.status_code == 200
    r = client.get(f"/api/cases/{case['id']}")
    assert r.json()["status"] == "reviewed"


def test_upload_rejects_bad_type():
    case = make_case(title="upload")
    r = client.post(
        f"/api/cases/{case['id']}/evidence",
        data={"kind": "screenshot"},
        files={"file": ("x.exe", b"MZ...", "application/x-msdownload")},
    )
    assert r.status_code == 415


def test_transcript_upload_creates_messages():
    case = make_case(title="transcript")
    transcript = (
        "caller: I am from CBI, your Aadhaar was used in a crime.\n"
        "victim: What? I didn't do anything.\n"
        "caller: Do not tell your family. Transfer Rs 20,000 to the safe account now.\n"
    )
    r = client.post(
        f"/api/cases/{case['id']}/evidence",
        data={"kind": "transcript"},
        files={"file": ("t.txt", transcript.encode(), "text/plain")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["assessment"] is not None
    r = client.get(f"/api/cases/{case['id']}")
    assert len(r.json()["messages"]) == 3


def test_simulated_alert_is_labelled():
    case = make_case(title="alert")
    r = client.post(f"/api/cases/{case['id']}/simulate-alert")
    assert r.status_code == 200
    assert r.json()["simulated"] is True
