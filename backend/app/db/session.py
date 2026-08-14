"""
Database connection layer for EngineerAI.

Engine-agnostic by design: the only thing that needs to change to migrate
from SQLite (temporary local development) to PostgreSQL (the approved
long-term architecture) is the DATABASE_URL environment variable, plus
removal of the one SQLite-only setting explicitly marked below.
"""

from typing import Generator

from sqlmodel import Session, create_engine

from app.core.config import settings

DATABASE_URL = settings.database_url

# --- SQLite-only setting -------------------------------------------------
# SQLite, by default, only allows a connection to be used by the thread that
# created it. Web frameworks may hand a request to a different thread than
# the one that opened the connection, so this flag relaxes that restriction
# for local development.
#
# REMOVE THIS BLOCK when migrating to PostgreSQL — it does not apply to,
# and is not needed by, any non-SQLite database.
connect_args: dict = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
# ---------------------------------------------------------------------------

engine = create_engine(DATABASE_URL, connect_args=connect_args)


def get_session() -> Generator[Session, None, None]:
    """
    Reusable session getter. Not yet wired into any API route (the first
    route is Task 8's health check), but written now as a generator so it
    can be used directly as a FastAPI dependency later without modification.
    """
    with Session(engine) as session:
        yield session


# --- Forward-compatibility note for Task 5 (domain models) ---------------
# When defining table models (users, projects, conversations, messages, and
# later knowledge_entries), use SQLAlchemy/SQLModel's generic JSON column
# type for any flexible/structured field (e.g. `structured_output`,
# knowledge entry payloads). Do NOT use PostgreSQL's JSONB type — JSON maps
# correctly to both SQLite and PostgreSQL, so model code will not need to
# change when the database engine is swapped later.
# ---------------------------------------------------------------------------
