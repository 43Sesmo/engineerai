"""
Conversations API — open and retrieve conversations within a project.

No auth system exists yet. Unlike Task 9's project endpoints, these routes
don't perform a default-user lookup at all: creation is scoped by the
existing project's id, and the approved plan only requires validating that
the parent project exists — not that it belongs to any particular user
(there's only one user, and no current-user concept to enforce yet). This
file deliberately stays independent from app/api/projects.py: no User
import, no reuse or duplication of Task 9's default-user helper.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, SQLModel, select

from app.db.models import Conversation, Project
from app.db.session import get_session

router = APIRouter(prefix="/api")


class ConversationCreate(SQLModel):
    title: Optional[str] = None


class ConversationRead(SQLModel):
    id: int
    project_id: int
    title: Optional[str]
    created_at: datetime


def _get_project_or_404(project_id: int, session: Session) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(
            status_code=404, detail=f"Project {project_id} not found."
        )
    return project


@router.post(
    "/projects/{project_id}/conversations",
    response_model=ConversationRead,
    status_code=201,
)
def create_conversation(
    project_id: int,
    payload: ConversationCreate,
    session: Session = Depends(get_session),
) -> Conversation:
    _get_project_or_404(project_id, session)
    conversation = Conversation(project_id=project_id, title=payload.title)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


@router.get(
    "/projects/{project_id}/conversations",
    response_model=List[ConversationRead],
)
def list_conversations(
    project_id: int, session: Session = Depends(get_session)
) -> List[Conversation]:
    """
    List conversations for a project, most-recent-first (Sprint 4 §3.3).
    Added to support the conversation list view — the create/get-by-id
    routes above already existed; this was the missing piece that made
    reopening or browsing past conversations impossible.
    """
    _get_project_or_404(project_id, session)
    return session.exec(
        select(Conversation)
        .where(Conversation.project_id == project_id)
        .order_by(Conversation.created_at.desc())
    ).all()


@router.get("/conversations/{conversation_id}", response_model=ConversationRead)
def get_conversation(
    conversation_id: int, session: Session = Depends(get_session)
) -> Conversation:
    conversation = session.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=404, detail=f"Conversation {conversation_id} not found."
        )
    return conversation
