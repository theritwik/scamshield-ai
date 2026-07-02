"""Generate a sample evidence PDF from the seeded critical demo case.

Usage:  python scripts/generate_demo_report.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "api"))

from app.database import SessionLocal  # noqa: E402
from app.models import Case  # noqa: E402
from app.services.report import generate_pdf, sha256_file  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        case = (
            db.query(Case)
            .filter(Case.severity == "Critical", Case.is_demo_seed.is_(True))
            .first()
        )
        if not case:
            print("No seeded critical case found. Run: python scripts/seed_data.py")
            raise SystemExit(1)
        path = generate_pdf(db, case)
        print(f"Report: {path}")
        print(f"SHA-256: {sha256_file(path)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
