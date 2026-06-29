from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile, status

from app.api.deps import CurrentUser, DbSession, FlexibleUser
from app.db.models.asset import AssetKind
from app.schemas.asset import AssetRead, AssetUpdate
from app.services import asset_service, project_service
from app.storage import get_storage

router = APIRouter(tags=["assets"])

# Inline uploads are capped to keep memory bounded (generated clips are small).
MAX_UPLOAD_BYTES = 200 * 1024 * 1024  # 200 MB


def _to_read(asset) -> AssetRead:
    data = AssetRead.model_validate(asset)
    data.url = asset_service.content_url(asset.id)
    return data


@router.post(
    "/projects/{project_id}/assets",
    response_model=AssetRead,
    status_code=201,
)
async def upload_asset(
    project_id: str,
    current_user: CurrentUser,
    db: DbSession,
    file: Annotated[UploadFile, File()],
) -> AssetRead:
    project = project_service.get(db, current_user.id, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 200MB).")
    if not data:
        raise HTTPException(status_code=400, detail="Empty file.")

    asset = asset_service.create_from_upload(
        db,
        project,
        filename=file.filename or "upload",
        data=data,
        content_type=file.content_type or "application/octet-stream",
    )
    return _to_read(asset)


@router.get("/projects/{project_id}/assets", response_model=list[AssetRead])
def list_assets(
    project_id: str,
    current_user: CurrentUser,
    db: DbSession,
    kind: Annotated[AssetKind | None, Query()] = None,
) -> list[AssetRead]:
    project = project_service.get(db, current_user.id, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return [_to_read(a) for a in asset_service.list_for_project(db, project_id, kind=kind)]


@router.get("/assets/{asset_id}", response_model=AssetRead)
def get_asset(
    asset_id: str, current_user: CurrentUser, db: DbSession
) -> AssetRead:
    asset = asset_service.get_for_owner(db, current_user.id, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found.")
    return _to_read(asset)


@router.patch("/assets/{asset_id}", response_model=AssetRead)
def rename_asset(
    asset_id: str, data: AssetUpdate, current_user: CurrentUser, db: DbSession
) -> AssetRead:
    asset = asset_service.get_for_owner(db, current_user.id, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found.")
    asset.name = data.name
    db.commit()
    db.refresh(asset)
    return _to_read(asset)


@router.get("/assets/{asset_id}/content")
def asset_content(
    asset_id: str, current_user: FlexibleUser, db: DbSession
) -> Response:
    asset = asset_service.get_for_owner(db, current_user.id, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found.")
    try:
        body = get_storage().get(asset.storage_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Asset bytes missing.") from exc
    return Response(
        content=body,
        media_type=asset.content_type,
        headers={"Cache-Control": "private, max-age=3600"},
    )


@router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    asset_id: str, current_user: CurrentUser, db: DbSession
) -> Response:
    asset = asset_service.get_for_owner(db, current_user.id, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found.")
    asset_service.delete(db, asset)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
