"""
Vault retrieval for the reasoning layer (Sprint 8).

Owns the KnowledgeEntry query and the text formatting of retrieved
context, so engine.py stays free of app.db imports and messages.py stays
free of prompt text. Fails soft: any error returns None, matching
parser.py's graceful-degradation convention — a Vault problem must
never break the core chat flow.

Transaction ownership stays with the caller. On PostgreSQL, a failed
query would leave the transaction aborted, so revisit fail-soft handling
in messages.py at the PostgreSQL migration.

MVP scope (approved): all entry types, most recent first, hard cap,
no embeddings, no entry_type filtering.
"""

import logging
from typing import Optional

from sqlmodel import Session, select

from app.db.models import KnowledgeEntry

logger = logging.getLogger(__name__)

DEFAULT_CAP = 5
MAX_ENTRY_CHARS = 300


def _looks_like_json(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith("{") or stripped.startswith("[")


def _truncate(text: str, limit: int) -> str:
    flat = " ".join(text.split())
    if len(flat) <= limit:
        return flat
    return flat[: limit - 1].rstrip() + "…"


def _entry_body(entry: KnowledgeEntry) -> Optional[str]:
    """engineering_reasoning if present, else a non-JSON summary, else None."""
    content = entry.content
    if isinstance(content, dict):
        reasoning = content.get("engineering_reasoning")
        if isinstance(reasoning, str) and reasoning.strip():
            return reasoning
    summary = entry.summary
    if isinstance(summary, str) and summary.strip() and not _looks_like_json(summary):
        return summary
    return None


def _format_entry(entry: KnowledgeEntry) -> Optional[str]:
    body = _entry_body(entry)
    if body is None:
        return None
    body = _truncate(body, MAX_ENTRY_CHARS)
    title = entry.title if isinstance(entry.title, str) else ""
    if title.strip() and not _looks_like_json(title):
        return f"- ({entry.entry_type}) {title.strip()}: {body}"
    return f"- ({entry.entry_type}) {body}"


def build_retrieved_context(
    session: Session, project_id: Optional[int], cap: int = DEFAULT_CAP
) -> Optional[str]:
    """
    Return a formatted context block from the project's most recent Vault
    entries, or None if there is nothing usable or anything goes wrong.

    The cap applies to rows fetched; entries skipped by the JSON guard are
    not backfilled (deliberate MVP simplicity).
    """
    if project_id is None:
        return None
    try:
        entries = session.exec(
            select(KnowledgeEntry)
            .where(KnowledgeEntry.project_id == project_id)
            .order_by(KnowledgeEntry.created_at.desc())
            .limit(cap)
        ).all()
        lines = [line for line in (_format_entry(e) for e in entries) if line]
        return "\n".join(lines) if lines else None
    except Exception:
        logger.warning("Vault retrieval failed; continuing without it.", exc_info=True)
        return None
