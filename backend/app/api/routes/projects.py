from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.project import (
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    ProjectWithStats,
)
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])


def _with_stats(project, count: int) -> ProjectWithStats:
    data = ProjectWithStats.model_validate(project)
    data.asset_count = count
    return data


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(
    data: ProjectCreate, current_user: CurrentUser, db: DbSession
) -> ProjectRead:
    project = project_service.create(db, current_user.id, data)
    return ProjectRead.model_validate(project)


@router.get("", response_model=list[ProjectWithStats])
def list_projects(
    current_user: CurrentUser,
    db: DbSession,
    search: Annotated[str | None, Query()] = None,
    sort: Annotated[Literal["recent", "oldest", "name"], Query()] = "recent",
) -> list[ProjectWithStats]:
    rows = project_service.list_for_owner(
        db, current_user.id, search=search, sort=sort
    )
    return [_with_stats(p, c) for p, c in rows]


@router.get("/{project_id}", response_model=ProjectWithStats)
def get_project(
    project_id: str, current_user: CurrentUser, db: DbSession
) -> ProjectWithStats:
    project = project_service.get(db, current_user.id, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    count = project_service.asset_count(db, project.id)
    return _with_stats(project, count)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: str,
    data: ProjectUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> ProjectRead:
    project = project_service.get(db, current_user.id, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    project = project_service.update(db, project, data)
    return ProjectRead.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str, current_user: CurrentUser, db: DbSession
) -> Response:
    project = project_service.get(db, current_user.id, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    project_service.delete(db, project)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{project_id}/duplicate", response_model=ProjectRead, status_code=201)
def duplicate_project(
    project_id: str, current_user: CurrentUser, db: DbSession
) -> ProjectRead:
    project = project_service.get(db, current_user.id, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    copy = project_service.duplicate(db, project)
    return ProjectRead.model_validate(copy)
