from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DbSession
from app.schemas.timeline import TimelineDocument, TimelineRead
from app.services import project_service, timeline_service

router = APIRouter(tags=["timeline"])


@router.get("/projects/{project_id}/timeline", response_model=TimelineRead)
def get_timeline(
    project_id: str, current_user: CurrentUser, db: DbSession
) -> TimelineRead:
    project = project_service.get(db, current_user.id, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    tv = timeline_service.get_current(db, project_id)
    return TimelineRead.model_validate(tv)


@router.put("/projects/{project_id}/timeline", response_model=TimelineRead)
def save_timeline(
    project_id: str,
    document: TimelineDocument,
    current_user: CurrentUser,
    db: DbSession,
) -> TimelineRead:
    project = project_service.get(db, current_user.id, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    tv = timeline_service.save(
        db, project_id, document.model_dump(mode="json")
    )
    return TimelineRead.model_validate(tv)
