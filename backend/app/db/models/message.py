"""
Message table — a single turn (user or assistant) within a conversation.

`structured_output` uses SQLAlchemy's generic JSON type, never PostgreSQL's
JSONB, so this model works unchanged across the SQLite/PostgreSQL
substitution documented in docs/vision.md. Nothing writes to this field
yet — it exists so Sprint 2's Reasoning Layer has somewhere to store
clarifying_questions, engineering_reasoning, preliminary_calculations,
material_suggestions, manufacturing_suggestions, and recommended_next_steps.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.db.models.conversation import Conversation


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversations.id")
    role: str  # "user" or "assistant"
    content_text: str
    structured_output: Optional[Dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON)
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    conversation: Optional["Conversation"] = Relationship(back_populates="messages")
