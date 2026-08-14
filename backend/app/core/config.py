"""
Centralized application settings for EngineerAI's backend.

This is the single place `.env` is loaded from. All other modules that need
configuration import `settings` from here rather than reading environment
variables directly — this keeps environment/config loading in exactly one
place in the codebase.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Required — no default. Must be provided via backend/.env.
    # Temporary SQLite value during local development; will point at
    # PostgreSQL once the approved long-term architecture is adopted.
    database_url: str

    # Optional — unused until Task 7 (AI Layer: Claude Client Wrapper).
    # Left blank by default rather than given a placeholder value that
    # could be mistaken for a real key.
    claude_api_key: str = ""

    # Optional — local dev server port, with a sensible default.
    server_port: int = 8000


settings = Settings()
