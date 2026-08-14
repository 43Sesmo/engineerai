"""
Seeds the single default user Sprint 1 needs.

Auth is deferred (single-user system for now), but every other table
already carries a user_id foreign key, so something real needs to exist
for them to reference. Safe to run more than once — it checks for an
existing user first rather than inserting a duplicate.

Usage (from the backend/ directory):
    python app/db/seed.py
"""

from sqlmodel import Session, select

from app.db.models import User
from app.db.session import engine


def seed_default_user() -> None:
    with Session(engine) as session:
        existing = session.exec(select(User)).first()
        if existing is not None:
            print(
                f"Default user already exists "
                f"(id={existing.id}, name={existing.name!r}) — skipping."
            )
            return

        # Placeholder name — a stand-in until real auth exists, not a
        # personalization decision baked into the schema.
        user = User(name="Founder")
        session.add(user)
        session.commit()
        session.refresh(user)
        print(f"Created default user (id={user.id}, name={user.name!r}).")


if __name__ == "__main__":
    seed_default_user()
