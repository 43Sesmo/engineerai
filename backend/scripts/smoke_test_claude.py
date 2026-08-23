"""
Standalone smoke test for the AI Layer's client.

Run this to confirm credentials, network access, and the active provider
(set via AI_PROVIDER in .env) all work correctly, independent of the rest
of the app — no database, no FastAPI server needed. Filename kept as
smoke_test_claude.py rather than renamed — it now exercises whichever
provider is configured, not exclusively Claude, but renaming the file
itself was judged unnecessary churn for this change.

Usage (run from the backend/ directory):
    python scripts/smoke_test_claude.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ai.client import AIProviderError, send_prompt  # noqa: E402


def main() -> None:
    prompt = "Reply with exactly the words: EngineerAI connection successful."
    print("Sending test prompt to the configured AI provider...")

    try:
        reply = send_prompt(prompt)
    except AIProviderError as exc:
        print(f"FAILED — {exc}")
        sys.exit(1)

    print()
    print("Provider replied:")
    print(reply)
    print()
    print("PASS — AI provider connectivity confirmed.")


if __name__ == "__main__":
    main()
