"""Edit-layer persistence + dispatch."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import EditLayer, Project
from app.schemas.edit_layer import EditLayerCreate, EditLayerUpdate
from app.services import edit_runner


def create(db: Session, project: Project, data: EditLayerCreate) -> EditLayer:
    # New layers stack on top of any existing ones for the clip.
    existing = list_for_clip(db, project.id, data.clip_id)
    position = (max((e.position for e in existing), default=-1)) + 1
    layer = EditLayer(
        project_id=project.id,
        clip_id=data.clip_id,
        engine=data.engine,
        preset_id=data.preset_id,
        label=data.label,
        prompt=data.prompt,
        params=data.params or {},
        source_asset_id=data.source_asset_id,
        position=position,
    )
    db.add(layer)
    db.commit()
    db.refresh(layer)
    return layer


def dispatch(db: Session, layer: EditLayer, mask_base64: str | None) -> None:
    """Run inline (eager/dev/tests) or enqueue on Celery (worker)."""
    if settings.celery_task_always_eager:
        edit_runner.run_edit(db, layer, mask_base64)
        db.refresh(layer)
    else:
        # Persist the mask now (worker has no request body), then enqueue.
        if mask_base64:
            from app.storage import get_storage  # noqa: PLC0415

            mask = edit_runner._decode_mask(mask_base64)
            if mask is not None:
                key = f"projects/{layer.project_id}/edits/{layer.id}/mask.png"
                get_storage().put(key, mask, "image/png")
                layer.mask_storage_key = key
                db.commit()
        from app.workers.edit_tasks import run_edit_job  # noqa: PLC0415

        run_edit_job.delay(layer.id)


def list_for_clip(db: Session, project_id: str, clip_id: str) -> list[EditLayer]:
    return list(
        db.scalars(
            select(EditLayer)
            .where(
                EditLayer.project_id == project_id,
                EditLayer.clip_id == clip_id,
            )
            .order_by(EditLayer.position)
        )
    )


def get(db: Session, layer_id: str) -> EditLayer | None:
    return db.get(EditLayer, layer_id)


def update(db: Session, layer: EditLayer, data: EditLayerUpdate) -> EditLayer:
    if data.enabled is not None:
        layer.enabled = data.enabled
    if data.position is not None:
        layer.position = data.position
    if data.prompt is not None:
        layer.prompt = data.prompt
    db.commit()
    db.refresh(layer)
    return layer


def delete(db: Session, layer: EditLayer) -> None:
    db.delete(layer)
    db.commit()


def top_result_asset_id(db: Session, project_id: str, clip_id: str) -> str | None:
    """The result asset of the top-most enabled, succeeded layer for a clip.

    Used by export to substitute the edited media for the original.
    """
    from app.db.models.edit_layer import EditLayerStatus  # noqa: PLC0415

    layers = [
        e
        for e in list_for_clip(db, project_id, clip_id)
        if e.enabled and e.status == EditLayerStatus.SUCCEEDED and e.result_asset_id
    ]
    if not layers:
        return None
    return layers[-1].result_asset_id
