"""
Knowledge Vault API — create, list, and get-by-id for KnowledgeEntry rows.

No auth system exists yet: follows the same single-default-user pattern
as projects.py.
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, SQLModel, select

from app.db.models import KnowledgeEntry, User
from app.db.session import get_session

router = APIRouter(prefix="/api")


class KnowledgeEntryCreate(SQLModel):
    project_id: Optional[int] = None
    source_conversation_id: Optional[int] = None
    source_message_id: Optional[int] = None
    entry_type: str
    title: str
    summary: str
    content: Optional[Dict] = None
    tags: Optional[List[str]] = None


class KnowledgeEntryRead(SQLModel):
    id: int
    user_id: int
    project_id: Optional[int]
    source_conversation_id: Optional[int]
    source_message_id: Optional[int]
    entry_type: str
    title: str
    summary: str
    content: Optional[Dict]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime


def _get_default_user(session: Session) -> User:
    """Mirrors projects.py's _get_default_user exactly — same lookup,
    same error, no duplicated divergent logic."""
    user = session.exec(select(User)).first()
    if user is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "No user found. Run `python -m app.db.seed` from backend/ "
                "to create the default user before using this endpoint."
            ),
        )
    return user


@router.post("/knowledge", response_model=KnowledgeEntryRead, status_code=201)
def create_knowledge_entry(
    payload: KnowledgeEntryCreate, session: Session = Depends(get_session)
) -> KnowledgeEntry:
    user = _get_default_user(session)
    entry = KnowledgeEntry(user_id=user.id, **payload.dict())
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@router.get("/knowledge", response_model=List[KnowledgeEntryRead])
def list_knowledge_entries(
    entry_type: Optional[str] = None,
    project_id: Optional[int] = None,
    session: Session = Depends(get_session),
) -> List[KnowledgeEntry]:
    user = _get_default_user(session)
    query = select(KnowledgeEntry).where(KnowledgeEntry.user_id == user.id)
    if entry_type is not None:
        query = query.where(KnowledgeEntry.entry_type == entry_type)
    if project_id is not None:
        query = query.where(KnowledgeEntry.project_id == project_id)
    return session.exec(query).all()


@router.get("/knowledge/{entry_id}", response_model=KnowledgeEntryRead)
def get_knowledge_entry(
    entry_id: int, session: Session = Depends(get_session)
) -> KnowledgeEntry:
    entry = session.get(KnowledgeEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return entry
