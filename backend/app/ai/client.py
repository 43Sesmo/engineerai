"""
AI Layer — thin wrapper around the Claude API.

Deliberately minimal: one function that sends a prompt and returns the raw
text response. No prompt engineering, no structured-output parsing, no
retrieval-augmentation — that's the Engineering Reasoning Layer's job in
Sprint 2, not this module's. This wrapper's only responsibility is proving
reliable, well-handled connectivity to Claude.
"""

import anthropic

from app.core.config import settings

DEFAULT_MODEL = "claude-sonnet-5"


class ClaudeClientError(Exception):
    """Raised when a Claude API call fails, wrapping the underlying cause."""


def send_prompt(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """
    Send a single prompt to Claude and return its raw text response.

    Raises ClaudeClientError — never a bare or swallowed exception — on any
    failure: a missing API key, a timeout, or an API error. Callers get a
    clear, actionable message rather than a silent failure or a raw SDK
    traceback.
    """
    if not settings.claude_api_key:
        raise ClaudeClientError(
            "CLAUDE_API_KEY is not set. Copy backend/.env.example to "
            "backend/.env and set CLAUDE_API_KEY before calling the AI layer."
        )

    client = anthropic.Anthropic(api_key=settings.claude_api_key)

    try:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APITimeoutError as exc:
        raise ClaudeClientError(f"Claude API request timed out: {exc}") from exc
    except anthropic.APIError as exc:
        raise ClaudeClientError(f"Claude API returned an error: {exc}") from exc

    text_parts = [block.text for block in response.content if block.type == "text"]
    return "".join(text_parts)
