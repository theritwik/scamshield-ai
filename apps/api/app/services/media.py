"""Multimodal ingestion adapters: OCR, QR decoding and audio transcription.

Each adapter reports the provider it used. When a real engine (Tesseract,
pyzbar, Whisper API) is unavailable, a clearly labelled mock provider keeps the
demo functional — mock output is marked ``provider: mock`` and shown as
simulated in the UI.
"""
import io
import re

from ..config import OPENAI_API_KEY

try:
    import pytesseract
    from PIL import Image

    pytesseract.get_tesseract_version()
    _HAS_TESSERACT = True
except Exception:  # pragma: no cover - environment dependent
    _HAS_TESSERACT = False

try:
    from pyzbar import pyzbar
    from PIL import Image as _QImage

    _HAS_ZBAR = True
except Exception:  # pragma: no cover - environment dependent
    _HAS_ZBAR = False


def ocr_image(data: bytes) -> dict:
    """Extract text from a screenshot. Falls back to a labelled mock."""
    if _HAS_TESSERACT:
        try:
            img = Image.open(io.BytesIO(data))
            text = pytesseract.image_to_string(img, lang="eng")
            return {"provider": "tesseract", "text": text.strip(), "confidence": "medium"}
        except Exception as exc:
            return {"provider": "tesseract", "text": "", "confidence": "failed", "error": str(exc)[:200]}
    return {
        "provider": "mock",
        "text": (
            "[SIMULATED OCR] Dear customer, your account will be blocked in 2 hours. "
            "Complete KYC immediately: http://kyc-sbi-update.example-fraud.in "
            "Helpline 9812345670"
        ),
        "confidence": "simulated",
        "note": "Tesseract not available in this environment; simulated output is clearly labelled.",
    }


def decode_qr(data: bytes) -> dict:
    """Decode a QR image. Never opens or executes the payload."""
    if _HAS_ZBAR:
        try:
            img = _QImage.open(io.BytesIO(data))
            results = pyzbar.decode(img)
            payloads = [r.data.decode("utf-8", errors="replace") for r in results]
            return {
                "provider": "pyzbar",
                "payloads": payloads,
                "upi": [_parse_upi(p) for p in payloads if p.lower().startswith("upi:")],
            }
        except Exception as exc:
            return {"provider": "pyzbar", "payloads": [], "error": str(exc)[:200]}
    payload = "upi://pay?pa=rbi.verify@ybl&pn=RBI%20Verification&am=50000"
    return {
        "provider": "mock",
        "payloads": [payload],
        "upi": [_parse_upi(payload)],
        "note": "zbar not available; simulated payload is clearly labelled.",
    }


def _parse_upi(payload: str) -> dict:
    params = dict(re.findall(r"[?&]([a-z]{2})=([^&]+)", payload, re.IGNORECASE))
    return {
        "payee_address": params.get("pa", ""),
        "payee_name": params.get("pn", "").replace("%20", " "),
        "amount": params.get("am", ""),
        "raw": payload,
        "warning": "Do not pay to this destination. Extracted for analysis only.",
    }


def transcribe_audio(data: bytes, filename: str) -> dict:
    """Transcribe audio via the OpenAI Whisper API when configured, else mock."""
    if OPENAI_API_KEY:
        try:
            import urllib.request

            boundary = "----scamshield"
            body = io.BytesIO()
            for name, value in (("model", "whisper-1"),):
                body.write(
                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode()
                )
            body.write(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
                f"Content-Type: application/octet-stream\r\n\r\n".encode()
            )
            body.write(data)
            body.write(f"\r\n--{boundary}--\r\n".encode())
            req = urllib.request.Request(
                "https://api.openai.com/v1/audio/transcriptions",
                data=body.getvalue(),
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                },
            )
            import json

            with urllib.request.urlopen(req, timeout=60) as resp:
                out = json.loads(resp.read())
            return {"provider": "openai-whisper", "text": out.get("text", ""), "confidence": "high"}
        except Exception as exc:
            return {"provider": "openai-whisper", "text": "", "confidence": "failed", "error": str(exc)[:200]}
    return {
        "provider": "mock",
        "text": (
            "[SIMULATED TRANSCRIPT] This is Inspector Sharma from CBI Mumbai. Your Aadhaar is "
            "linked to a parcel containing illegal items. Do not disconnect this call and do not "
            "inform anyone. Transfer the verification amount to the safe RBI account immediately."
        ),
        "confidence": "simulated",
        "note": "No transcription API key configured; simulated transcript is clearly labelled.",
    }
