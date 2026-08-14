"""
Conversation table — a single reasoning session within a project.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.db.models.message import Message
    from app.db.models.project import Project


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id")
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    project: Optional["Project"] = Relationship(back_populates="conversations")
    messages: List["Message"] = Relationship(back_populates="conversation")
