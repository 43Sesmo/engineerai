"""
Projects API — create and list projects for the (currently single) user.

No auth system exists yet: every request here operates against the one
seeded default user (Task 6), looked up by querying for the first User
row rather than a hardcoded id, so this keeps working correctly
regardless of that row's actual id.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, SQLModel, select

from app.db.models import Project, User
from app.db.session import get_session

router = APIRouter(prefix="/api")


class ProjectCreate(SQLModel):
    title: str
    description: Optional[str] = None
    status: str = "exploring"


class ProjectRead(SQLModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime


def _get_default_user(session: Session) -> User:
    """
    Looks up the single seeded user by query, not a hardcoded id. Raises a
    clear error — not a raw database failure — if the seed hasn't been run.
    """
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


@router.post("/projects", response_model=ProjectRead, status_code=201)
def create_project(
    payload: ProjectCreate, session: Session = Depends(get_session)
) -> Project:
    user = _get_default_user(session)
    project = Project(
        user_id=user.id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.get("/projects", response_model=List[ProjectRead])
def list_projects(session: Session = Depends(get_session)) -> List[Project]:
    user = _get_default_user(session)
    projects = session.exec(
        select(Project).where(Project.user_id == user.id)
    ).all()
    return projects
