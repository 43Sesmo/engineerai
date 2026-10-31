"""
Anthropic provider implementation.

This is the only file in the codebase that imports `anthropic`. Any
Anthropic-SDK-specific exception is caught here and re-raised as the
shared, generic AIProviderError, so callers never need to know which
provider is active.

Sprint 9: the output budget (thinking and visible text share it) is
MAX_OUTPUT_TOKENS. A response that stops at the budget, or that carries no
text, now raises AIProviderError instead of being returned as a silent,
cut-off or empty string. A near-miss warning fires at NEAR_MISS_TOKENS.
Successful calls below that threshold log nothing.
"""

import logging

import anthropic

from app.ai.errors import AIProviderError
from app.core.config import settings

logger = logging.getLogger(__name__)

# Thinking and visible text share this budget. 10,240 was chosen from
# measured totals (largest observed 7,130) and an estimated worst-case wait
# of about two minutes; see the Sprint 9 planning document.
# V5 run 1 later reached this cap: 10,240 output tokens, 8,355 of them
# thinking (see the Sprint 9 closure report).
MAX_OUTPUT_TOKENS = 10240

# Reasoning effort sent with every request. Chosen after the Sprint 9 D2 and
# V10 measurements; see the Sprint 9 closure report. Effort is soft guidance,
# not a limit: MAX_OUTPUT_TOKENS above still bounds every call. Effort may be
# unavailable on other models, so check before changing the model.
EFFORT = "medium"

# Warn when a call that finished normally used at least this many output
# tokens, so creep toward the budget is visible before failures begin.
NEAR_MISS_TOKENS = 8192


def _thinking_tokens(response):
    usage = getattr(response, "usage", None)
    details = getattr(usage, "output_tokens_details", None)
    return getattr(details, "thinking_tokens", None)


def send_prompt(prompt: str, model: str | None = None) -> str:
    """
    Send a single prompt to Claude and return its raw text response.

    Raises AIProviderError — never a bare or swallowed exception — on any
    failure: a missing API key, a timeout, an API error, a response that
    stopped at the output budget, or a response with no text.
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
            max_tokens=MAX_OUTPUT_TOKENS,
            output_config={"effort": EFFORT},
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APITimeoutError as exc:
        raise AIProviderError(f"Anthropic API request timed out: {exc}") from exc
    except anthropic.APIError as exc:
        raise AIProviderError(f"Anthropic API returned an error: {exc}") from exc

    text = "".join(block.text for block in response.content if block.type == "text")
    stop = getattr(response, "stop_reason", None)
    out_tokens = getattr(getattr(response, "usage", None), "output_tokens", None)
    thinking = _thinking_tokens(response)
    blocks = [getattr(block, "type", "?") for block in response.content]

    if stop == "max_tokens":
        logger.warning(
            "Anthropic response truncated at max_tokens (model=%s, output_tokens=%s, "
            "thinking_tokens=%s, blocks=%s).",
            resolved_model, out_tokens, thinking, blocks,
        )
        raise AIProviderError(
            f"The model used its whole output budget ({MAX_OUTPUT_TOKENS:,} tokens, "
            "including its thinking) before finishing, so no usable answer was "
            "returned. Try again, or ask a narrower question."
        )

    if out_tokens is not None and out_tokens >= NEAR_MISS_TOKENS:
        logger.warning(
            "Anthropic response used %s of %s output tokens (near miss; model=%s, "
            "thinking_tokens=%s).",
            out_tokens, MAX_OUTPUT_TOKENS, resolved_model, thinking,
        )

    if not text.strip():
        logger.warning(
            "Anthropic returned no text (model=%s, stop_reason=%s, output_tokens=%s, "
            "thinking_tokens=%s, blocks=%s).",
            resolved_model, stop, out_tokens, thinking, blocks,
        )
        raise AIProviderError("The model returned no text. Try again.")

    return text
