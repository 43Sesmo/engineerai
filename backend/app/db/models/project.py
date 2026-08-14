"""
Project table — the top-level container for a body of engineering work.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.db.models.conversation import Conversation
    from app.db.models.user import User


class Project(SQLModel, table=True):
    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    title: str
    description: Optional[str] = None
    status: str = Field(default="exploring")  # exploring / active / archived
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: Optional["User"] = Relationship(back_populates="projects")
    conversations: List["Conversation"] = Relationship(back_populates="project")
