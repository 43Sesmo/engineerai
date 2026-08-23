"""
AI Layer — provider-agnostic facade.

Reads settings.ai_provider and delegates to the matching provider module.
Callers only ever import from this module — never a provider module or
either SDK directly — so switching providers is a one-line configuration
change (AI_PROVIDER in .env), never a code change anywhere else in the app.

Provider modules are imported lazily, inside each dispatch branch, not at
the top of this file — so this module never requires both the `anthropic`
and `openai` packages to be installed, only whichever one the configured
provider actually needs.
"""

from app.ai.errors import AIProviderError
from app.core.config import settings

__all__ = ["send_prompt", "AIProviderError"]


def send_prompt(prompt: str, model: str | None = None) -> str:
    if settings.ai_provider == "anthropic":
        from app.ai.providers import anthropic_provider

        return anthropic_provider.send_prompt(prompt, model=model)
    elif settings.ai_provider == "openai":
        from app.ai.providers import openai_provider

        return openai_provider.send_prompt(prompt, model=model)
    else:
        raise AIProviderError(
            f"Unknown AI provider configured: {settings.ai_provider!r}"
        )
