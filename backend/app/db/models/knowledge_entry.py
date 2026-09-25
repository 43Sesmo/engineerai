"""
KnowledgeEntry table — the Knowledge Vault's single unified store, across
all entry categories (decisions, lessons learned, design patterns,
research findings, engineering knowledge, user preferences).
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON


class KnowledgeEntry(SQLModel, table=True):
    __tablename__ = "knowledge_entries"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    project_id: Optional[int] = Field(default=None, foreign_key="projects.id")
    source_conversation_id: Optional[int] = Field(
        default=None, foreign_key="conversations.id"
    )
    source_message_id: Optional[int] = Field(
        default=None, foreign_key="messages.id"
    )
    entry_type: str
    title: str
    summary: str
    content: Optional[Dict] = Field(default=None, sa_column=Column(JSON))
    tags: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
