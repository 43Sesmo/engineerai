"""
Anthropic provider implementation.

This is the only file in the codebase that imports `anthropic`. Any
Anthropic-SDK-specific exception is caught here and re-raised as the
shared, generic AIProviderError, so callers never need to know which
provider is active.
"""

import anthropic

from app.ai.errors import AIProviderError
from app.core.config import settings


def send_prompt(prompt: str, model: str | None = None) -> str:
    """
    Send a single prompt to Claude and return its raw text response.

    Raises AIProviderError — never a bare or swallowed exception — on any
    failure: a missing API key, a timeout, or an API error.
    """
    if not settings.anthropic_api_key:
        raise AIProviderError(
            "ANTHROPIC_API_KEY is not set. Copy backend/.env.example to "
            "backend/.env and set ANTHROPIC_API_KEY before calling the AI "
            "layer. (CLAUDE_API_KEY is also still honored, if that's what "
            "your .env already has.)"
        )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    resolved_model = model or settings.anthropic_model

    try:
        response = client.messages.create(
            model=resolved_model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APITimeoutError as exc:
        raise AIProviderError(f"Anthropic API request timed out: {exc}") from exc
    except anthropic.APIError as exc:
        raise AIProviderError(f"Anthropic API returned an error: {exc}") from exc

    text_parts = [block.text for block in response.content if block.type == "text"]
    return "".join(text_parts)
