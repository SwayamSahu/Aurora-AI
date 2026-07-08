"""Edit-layer orchestration.

`run_edit(db, layer)` drives the video editor from the registry, streams
progress onto the EditLayer row, and persists the result as a derived Asset.
Used both inline (eager/dev/tests) and from the Celery worker — mirrors
`job_runner.run_generation`.
"""

from __future__ import annotations

import base64

from sqlalchemy.orm import Session

from app.db.models import Asset, EditLayer, Project
from app.db.models.asset import AssetKind, AssetSource
from app.db.models.edit_layer import EditLayerStatus
from app.generators.base import VideoEditParams
from app.generators.registry import get_video_editor
from app.services import asset_service
from app.storage import get_storage


def _decode_mask(raw: str | None) -> bytes | None:
    if not raw:
        return None
    # Accept either a bare base64 string or a data URL.
    if "," in raw and raw.strip().startswith("data:"):
        raw = raw.split(",", 1)[1]
    try:
        return base64.b64decode(raw)
    except (ValueError, TypeError):
        return None


def _set(db: Session, layer: EditLayer, **fields) -> None:
    for k, v in fields.items():
        setattr(layer, k, v)
    db.commit()
    db.refresh(layer)


def run_edit(
    db: Session, layer: EditLayer, mask_base64: str | None = None
) -> EditLayer:
    """Run the edit to completion, recording the outcome on the layer.

    Never raises: failures are captured on `layer.error` / status=FAILED.
    """
    project = db.get(Project, layer.project_id)
    if project is None:
        _set(
            db, layer, status=EditLayerStatus.FAILED, error="Project no longer exists."
        )
        return layer

    source = db.get(Asset, layer.source_asset_id) if layer.source_asset_id else None
    if source is None or source.project_id != project.id:
        _set(
            db,
            layer,
            status=EditLayerStatus.FAILED,
            error="Source clip asset not found.",
        )
        return layer

    _set(db, layer, status=EditLayerStatus.RUNNING, progress=0.0, error=None)

    def progress(fraction: float, message: str | None = None) -> None:
        _set(db, layer, progress=fraction)

    try:
        mask = _decode_mask(mask_base64)
        if mask is not None:
            key = f"projects/{project.id}/edits/{layer.id}/mask.png"
            get_storage().put(key, mask, "image/png")
            layer.mask_storage_key = key
            db.commit()

        src_bytes = get_storage().get(source.storage_key)
        params = VideoEditParams(
            source=src_bytes,
            source_content_type=source.content_type,
            engine=layer.engine,  # type: ignore[arg-type]
            prompt=layer.prompt,
            mask=mask,
            params=layer.params or {},
            preset_id=layer.preset_id,
        )
        media = get_video_editor().edit(params, progress)

        asset = asset_service.create_from_upload(
            db,
            project,
            filename=media.suggested_filename,
            data=media.data,
            content_type=media.content_type,
            source=AssetSource.DERIVED,
            kind=AssetKind.VIDEO,
            duration_seconds=media.duration_seconds or source.duration_seconds,
            width=media.width or source.width,
            height=media.height or source.height,
        )
        _set(
            db,
            layer,
            result_asset_id=asset.id,
            status=EditLayerStatus.SUCCEEDED,
            progress=1.0,
        )
    except Exception as exc:  # noqa: BLE001 — record any failure on the layer
        _set(db, layer, status=EditLayerStatus.FAILED, error=str(exc))
    return layer
