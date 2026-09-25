"""add knowledge_entries table

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("source_conversation_id", sa.Integer(), nullable=True),
        sa.Column("source_message_id", sa.Integer(), nullable=True),
        sa.Column("entry_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_knowledge_entries_user_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"],
            name=op.f("fk_knowledge_entries_project_id_projects"),
        ),
        sa.ForeignKeyConstraint(
            ["source_conversation_id"], ["conversations.id"],
            name=op.f("fk_knowledge_entries_source_conversation_id_conversations"),
        ),
        sa.ForeignKeyConstraint(
            ["source_message_id"], ["messages.id"],
            name=op.f("fk_knowledge_entries_source_message_id_messages"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_knowledge_entries")),
    )


def downgrade() -> None:
    op.drop_table("knowledge_entries")
