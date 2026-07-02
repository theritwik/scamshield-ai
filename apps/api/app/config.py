"""Application configuration loaded from environment variables."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent.parent
DATA_DIR = Path(os.environ.get("SCAMSHIELD_DATA_DIR", REPO_ROOT / "data"))
UPLOAD_DIR = Path(os.environ.get("SCAMSHIELD_UPLOAD_DIR", BASE_DIR / "uploads"))
REPORT_DIR = Path(os.environ.get("SCAMSHIELD_REPORT_DIR", BASE_DIR / "reports"))

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'scamshield.db'}")

# Demo-only investigator token. This is intentionally a static demo credential:
# the prototype ships no real authentication and says so in the UI.
INVESTIGATOR_DEMO_TOKEN = os.environ.get("INVESTIGATOR_DEMO_TOKEN", "demo-investigator")

# Optional external providers. The demo must work with none of these set.
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", 8 * 1024 * 1024))
ALLOWED_UPLOAD_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "text/plain": ".txt",
}

CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if o.strip()
]

ENGINE_VERSION = "scamshield-risk-engine/1.0.0"
