"""
Health check endpoint — the simplest possible proof the API server is
alive. Deliberately has no database or AI dependency: it must work even if
those are completely unavailable, since that's the whole point of a
liveness check.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api")


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok"}
