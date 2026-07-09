from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DbSession
from app.db.models import Asset
from app.generators.base import DetectParams
from app.generators.registry import get_object_detector
from app.schemas.detect import DetectedObjectRead, DetectRequest
from app.services import project_service
from app.storage import get_storage

router = APIRouter(tags=["detect"])


@router.post(
    "/projects/{project_id}/detect-objects",
    response_model=list[DetectedObjectRead],
)
def detect_objects(
    project_id: str,
    data: DetectRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> list[DetectedObjectRead]:
    project = project_service.get(db, current_user.id, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    if data.mode == "click" and (data.x is None or data.y is None):
        raise HTTPException(
            status_code=422, detail="'x' and 'y' are required for click mode."
        )
    if data.mode == "text" and not (data.query or "").strip():
        raise HTTPException(
            status_code=422, detail="'query' is required for text mode."
        )

    # Attach the clip's source bytes so real (CUDA) backends have a frame to
    # run on. The mock detector ignores them.
    source: bytes | None = None
    if data.asset_id:
        asset = db.get(Asset, data.asset_id)
        if asset is None or asset.project_id != project.id:
            raise HTTPException(status_code=404, detail="Source asset not found.")
        try:
            source = get_storage().get(asset.storage_key)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=502, detail="Could not read source asset."
            ) from exc

    results = get_object_detector().detect(
        DetectParams(
            mode=data.mode, x=data.x, y=data.y, query=data.query, source=source
        )
    )
    return [DetectedObjectRead.model_validate(r.__dict__) for r in results]
