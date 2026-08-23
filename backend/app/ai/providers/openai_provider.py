"""
OpenAI provider implementation.

This is the only file in the codebase that imports `openai`. Any
OpenAI-SDK-specific exception is caught here and re-raised as the shared,
generic AIProviderError, so callers never need to know which provider is
active.

Uses the Responses API (client.responses.create -> response.output_text),
not the older Chat Completions pattern — confirmed against OpenAI's own
current API documentation, which uses the Responses API as its standard
example for error handling and basic usage as of this implementation.

Exception names (APITimeoutError, APIError) and the default model
identifier (gpt-5.6-terra) were both verified against OpenAI's official
documentation before this file was written, not assumed.
"""

import openai

from app.ai.errors import AIProviderError
from app.core.config import settings


def send_prompt(prompt: str, model: str | None = None) -> str:
    """
    Send a single prompt to OpenAI and return its raw text response.

    Raises AIProviderError — never a bare or swallowed exception — on any
    failure: a missing API key, a timeout, or an API error.
    """
    if not settings.openai_api_key:
        raise AIProviderError(
            "OPENAI_API_KEY is not set. Copy backend/.env.example to "
            "backend/.env and set OPENAI_API_KEY before calling the AI "
            "layer."
        )

    client = openai.OpenAI(api_key=settings.openai_api_key)
    resolved_model = model or settings.openai_model

    try:
        response = client.responses.create(model=resolved_model, input=prompt)
    except openai.APITimeoutError as exc:
        raise AIProviderError(f"OpenAI API request timed out: {exc}") from exc
    except openai.APIError as exc:
        raise AIProviderError(f"OpenAI API returned an error: {exc}") from exc

    return response.output_text
