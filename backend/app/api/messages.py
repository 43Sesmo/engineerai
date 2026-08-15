"""
Messages API — the minimal round trip: post a message, store it, send it
to Claude, store the reply, return both.

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
from sqlmodel import Session, SQLModel, select

from app.ai.client import ClaudeClientError, send_prompt
from app.db.models import Conversation, Message
from app.db.session import get_session

router = APIRouter(prefix="/api")


class MessageCreate(SQLModel):
    content: str


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
    _get_conversation_or_404(conversation_id, session)

    # Store the user's message first and commit immediately — preserved
    # regardless of whether the Claude call below succeeds.
    user_message = Message(
        conversation_id=conversation_id, role="user", content_text=payload.content
    )
    session.add(user_message)
    session.commit()
    session.refresh(user_message)

    try:
        reply_text = send_prompt(payload.content)
    except ClaudeClientError as exc:
        raise HTTPException(
            status_code=502, detail=f"Claude API call failed: {exc}"
        ) from exc

    assistant_message = Message(
        conversation_id=conversation_id, role="assistant", content_text=reply_text
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
