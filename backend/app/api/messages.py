"""
Messages API — the minimal round trip: post a message, store it, send it
to Claude, store the reply, return both. Sprint 8: also fetches project Vault context via app.reasoning.retrieval and passes it through as an opaque string; formatting still lives outside this module.

No prompt engineering, no structured-output parsing — payload.content goes
to Claude exactly as typed, and the reply is stored exactly as returned.
That's Sprint 2's Engineering Reasoning Layer's job, not this module's.

Design decision (approved): the user's message is committed BEFORE the
Claude call, not rolled back if that call fails. A failed AI call returns
a clean 502 with the underlying error surfaced, but never erases what the
user typed — conversation history is preserved over strict atomicity.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import field_validator
from sqlmodel import Session, SQLModel, select

from app.ai.client import AIProviderError
from app.db.models import Conversation, Message
from app.db.session import get_session
from app.reasoning.engine import run_reasoning
from app.reasoning.retrieval import build_retrieved_context

router = APIRouter(prefix="/api")


class MessageCreate(SQLModel):
    content: str

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("content must not be empty or whitespace-only.")
        return value


class MessageRead(SQLModel):
    id: int
    conversation_id: int
    role: str
    content_text: str
    structured_output: Optional[dict] = None
    created_at: datetime


def _get_conversation_or_404(conversation_id: int, session: Session) -> Conversation:
    conversation = session.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=404, detail=f"Conversation {conversation_id} not found."
        )
    return conversation


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=List[MessageRead],
    status_code=201,
)
def create_message(
    conversation_id: int,
    payload: MessageCreate,
    session: Session = Depends(get_session),
) -> List[Message]:
    conversation = _get_conversation_or_404(conversation_id, session)
    project_id = conversation.project_id

    # Store the user's message first and commit immediately — preserved
    # regardless of whether the reasoning call below succeeds.
    user_message = Message(
        conversation_id=conversation_id, role="user", content_text=payload.content
    )
    session.add(user_message)
    session.commit()
    session.refresh(user_message)

    retrieved_context = build_retrieved_context(session, project_id)

    try:
        result = run_reasoning(payload.content, retrieved_context=retrieved_context)
    except AIProviderError as exc:
        raise HTTPException(
            status_code=502, detail=f"Reasoning engine call failed: {exc}"
        ) from exc

    structured_dict = (
        result.structured.model_dump() if result.structured is not None else None
    )

    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content_text=result.raw_text,
        structured_output=structured_dict,
    )
    session.add(assistant_message)
    session.commit()
    session.refresh(assistant_message)

    return [user_message, assistant_message]


@router.get(
    "/conversations/{conversation_id}/messages", response_model=List[MessageRead]
)
def list_messages(
    conversation_id: int, session: Session = Depends(get_session)
) -> List[Message]:
    _get_conversation_or_404(conversation_id, session)
    messages = session.exec(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    ).all()
    return messages
