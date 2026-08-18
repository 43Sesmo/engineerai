"""
EngineerAI backend — application entrypoint.

Task 8 added GET /api/health. Task 9 added POST/GET /api/projects. Task 10
added conversation create/get. Task 11 added the messages round trip —
the backend side of Sprint 1's core deliverable. Task 13 added CORS
middleware — the one necessary exception to "frontend tasks don't touch
the backend," required because browsers block cross-origin requests
(localhost:3000 calling localhost:8000 is cross-origin) without it.
FastAPI's automatic /docs and /openapi.json exist by default; that's
built-in framework behavior, not new scope added by any task.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import conversations, health, messages, projects
from app.core.config import settings

app = FastAPI(
    title="EngineerAI",
    description=(
        "A Personal AI Engineering Company designed to act as a lifelong "
        "engineering partner — transforming ideas, sketches, photos, "
        "drawings, and engineering requirements into manufacturable "
        "engineering solutions."
    ),
)

# Scoped narrowly to the frontend's actual origin and the methods that
# actually exist today — not wildcarded.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(projects.router)
app.include_router(conversations.router)
app.include_router(messages.router)


if __name__ == "__main__":
    # Convenience entrypoint for local development. The primary way to run
    # this app is `uvicorn app.main:app --reload` from the backend/
    # directory, which supports auto-reload; this path does not.
    uvicorn.run(app, host="0.0.0.0", port=settings.server_port)
