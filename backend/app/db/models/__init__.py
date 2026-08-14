"""
Import all domain models here so SQLModel/SQLAlchemy can resolve the
string-based relationship references between them (User <-> Project <->
Conversation <-> Message), and so Task 6's future Alembic setup has one
place to import from to discover every table.
"""

from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.db.models.project import Project
from app.db.models.user import User

__all__ = ["User", "Project", "Conversation", "Message"]
