"""
Standalone smoke test for the AI Layer's Claude client wrapper.

Run this to confirm credentials, network access, and the client wrapper
all work correctly, independent of the rest of the app — no database, no
FastAPI server needed.

Usage (run from the backend/ directory):
    python scripts/smoke_test_claude.py
"""

import os
import sys

# Allow running this script directly from backend/scripts/ by adding the
# backend/ directory to the path so `app` can be imported — same pattern
# as scripts/verify_sqlite_connection.py (Task 2). This avoids the
# ModuleNotFoundError hit during Task 6 when a script under app/ was run
# by direct file path instead of as a package.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ai.client import ClaudeClientError, send_prompt  # noqa: E402


def main() -> None:
    prompt = "Reply with exactly the words: EngineerAI connection successful."
    print("Sending test prompt to Claude...")

    try:
        reply = send_prompt(prompt)
    except ClaudeClientError as exc:
        print(f"FAILED — {exc}")
        sys.exit(1)

    print()
    print("Claude replied:")
    print(reply)
    print()
    print("PASS — Claude API connectivity confirmed.")


if __name__ == "__main__":
    main()
