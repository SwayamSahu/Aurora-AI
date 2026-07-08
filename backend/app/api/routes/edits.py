from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.deps import CurrentUser, DbSession
from app.db.models import Asset, EditLayer
from app.schemas.asset import AssetRead
from app.schemas.edit_layer import (
    EditLayerCreate,
    EditLayerRead,
    EditLayerUpdate,
)
from app.services import asset_service, edit_service, project_service

router = APIRouter(tags=["edits"])


def _to_read(db: DbSession, layer: EditLayer) -> EditLayerRead:
    data = EditLayerRead.model_validate(layer)
    if layer.result_asset_id:
        asset = db.get(Asset, layer.result_asset_id)
        if asset is not None:
            ar = AssetRead.model_validate(asset)
            ar.url = asset_service.content_url(asset.id)
            data.result_asset = ar
    return data


def _owned_layer(db: DbSession, user_id: str, layer_id: str) -> EditLayer:
    layer = edit_service.get(db, layer_id)
    if layer is None or project_service.get(db, user_id, layer.project_id) is None:
        raise HTTPException(status_code=404, detail="Edit layer not found.")
    return layer


@router.post(
    "/projects/{project_id}/edits",
    response_model=EditLayerRead,
    status_code=201,
)
def create_edit(
    project_id: str,
    data: EditLayerCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> EditLayerRead:
    project = project_service.get(db, current_user.id, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    layer = edit_service.create(db, project, data)
    edit_service.dispatch(db, layer, data.mask_base64)
    return _to_read(db, layer)


@router.get("/projects/{project_id}/edits", response_model=list[EditLayerRead])
def list_edits(
    project_id: str,
    current_user: CurrentUser,
    db: DbSession,
    clip_id: Annotated[str, Query()],
) -> list[EditLayerRead]:
    project = project_service.get(db, current_user.id, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    layers = edit_service.list_for_clip(db, project_id, clip_id)
    return [_to_read(db, e) for e in layers]


@router.get("/edits/{layer_id}", response_model=EditLayerRead)
def get_edit(layer_id: str, current_user: CurrentUser, db: DbSession) -> EditLayerRead:
    layer = _owned_layer(db, current_user.id, layer_id)
    return _to_read(db, layer)


@router.patch("/edits/{layer_id}", response_model=EditLayerRead)
def update_edit(
    layer_id: str,
    data: EditLayerUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> EditLayerRead:
    layer = _owned_layer(db, current_user.id, layer_id)
    layer = edit_service.update(db, layer, data)
    return _to_read(db, layer)


@router.delete("/edits/{layer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_edit(layer_id: str, current_user: CurrentUser, db: DbSession) -> Response:
    layer = _owned_layer(db, current_user.id, layer_id)
    edit_service.delete(db, layer)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
