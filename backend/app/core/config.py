"""
Centralized application settings for EngineerAI's backend.

This is the single place `.env` is loaded from. All other modules that need
configuration import `settings` from here rather than reading environment
variables directly — this keeps environment/config loading in exactly one
place in the codebase.
"""

from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Required — no default. Must be provided via backend/.env.
    # Temporary SQLite value during local development; will point at
    # PostgreSQL once the approved long-term architecture is adopted.
    database_url: str

    # Optional — local dev server port, with a sensible default.
    server_port: int = 8000

    # --- AI Provider Abstraction --------------------------------------
    # Which provider send_prompt() uses. Config-only selection, no
    # runtime/per-request switching.
    ai_provider: Literal["anthropic", "openai"] = "anthropic"

    # ANTHROPIC_API_KEY is checked first; CLAUDE_API_KEY (the old name)
    # is still honored if that's what an existing .env already has, so
    # nothing breaks for anyone who hasn't updated their .env yet.
    anthropic_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("ANTHROPIC_API_KEY", "CLAUDE_API_KEY"),
    )
    anthropic_model: str = "claude-sonnet-5"

    openai_api_key: str = ""
    openai_model: str = "gpt-5.6-terra"


settings = Settings()
