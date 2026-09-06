"""
Standalone smoke test for the reasoning engine's orchestration path.

Sends a real test idea through generate_guidance() — build_prompt() +
send_prompt() together — and prints the raw response. Confirms the full
prompt (including Task 2's worked example) actually gets a coherent
response from whichever provider is configured, before Task 4's parser
is built on top of an unverified assumption.

Usage (run from the backend/ directory):
    python scripts/smoke_test_reasoning_engine.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ai.client import AIProviderError  # noqa: E402
from app.reasoning.engine import generate_guidance  # noqa: E402


def main() -> None:
    test_input = "I need a shaft to transmit 5 kW at 300 rpm."
    print(f"Sending test idea through the reasoning engine: {test_input!r}")

    try:
        raw_response = generate_guidance(test_input)
    except AIProviderError as exc:
        print(f"FAILED — {exc}")
        sys.exit(1)

    print()
    print("Raw response:")
    print(raw_response)
    print()
    print(
        f"PASS — reasoning engine orchestration confirmed "
        f"({len(raw_response)} characters)."
    )


if __name__ == "__main__":
    main()
