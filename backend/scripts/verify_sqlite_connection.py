"""
Standalone verification script for the SQLite local development database.

Run this after `pip install -r requirements.txt` and after copying
`.env.example` to `.env`, to confirm the database connection layer works
before any application code depends on it.

Usage (run from the backend/ directory):
    python scripts/verify_sqlite_connection.py
"""

import os
import sys

# Allow running this script directly from backend/scripts/ by adding the
# backend/ directory to the path so `app` can be imported.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlmodel import text  # noqa: E402

from app.db.session import DATABASE_URL, engine  # noqa: E402


def main() -> None:
    print("Verifying SQLite database connection...")
    print(f"  DATABASE_URL: {DATABASE_URL}")

    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.scalar()
            assert value == 1, f"Expected 1, got {value}"
        print("  Connection: OK (SELECT 1 succeeded)")
    except Exception as exc:
        print(f"  Connection: FAILED — {exc}")
        sys.exit(1)

    if DATABASE_URL.startswith("sqlite:///"):
        db_path = DATABASE_URL.replace("sqlite:///", "", 1)
        abs_path = os.path.abspath(db_path)
        if os.path.exists(abs_path):
            print(f"  Database file: OK ({abs_path})")
        else:
            print(f"  Database file: NOT FOUND at expected path {abs_path}")
            print("  (Make sure you're running this script from the backend/ directory.)")
            sys.exit(1)

    print()
    print("PASS — SQLite connection layer is working correctly.")


if __name__ == "__main__":
    main()
