"""
User table.

Single-row for now (the founder is the only user), but every other table
already carries a user_id foreign key so multi-user support later is an
additive change, not a schema redesign.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.db.models.project import Project


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    projects: List["Project"] = Relationship(back_populates="user")
