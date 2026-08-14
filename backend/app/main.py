"""
EngineerAI backend — application entrypoint.

Task 8 added the first route: GET /api/health. Task 9 added the second:
POST/GET /api/projects. Every other route belongs to later tasks (Tasks
10-11). FastAPI's automatic /docs and /openapi.json exist by default;
that's built-in framework behavior, not new scope added by any task.
"""

import uvicorn
from fastapi import FastAPI

from app.api import health, projects
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

app.include_router(health.router)
app.include_router(projects.router)


if __name__ == "__main__":
    # Convenience entrypoint for local development. The primary way to run
    # this app is `uvicorn app.main:app --reload` from the backend/
    # directory, which supports auto-reload; this path does not.
    uvicorn.run(app, host="0.0.0.0", port=settings.server_port)
