"""Celery task for AI edit-layer jobs.

Opens its own DB session (worker process) and delegates to the pure
`run_edit` orchestrator. Inline/eager execution (dev/tests) calls `run_edit`
directly with the request session instead — see edit_service.dispatch.
"""

from __future__ import annotations

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.services import edit_runner


@celery_app.task(name="aurora.run_edit_job")
def run_edit_job(layer_id: str) -> str:
    from app.db.models import EditLayer  # local import to avoid circulars

    db = SessionLocal()
    try:
        layer = db.get(EditLayer, layer_id)
        if layer is None:
            return "missing"
        # Mask was already persisted by dispatch(); reload from storage.
        mask_b64 = None
        if layer.mask_storage_key:
            import base64  # noqa: PLC0415

            from app.storage import get_storage  # noqa: PLC0415

            mask_b64 = base64.b64encode(
                get_storage().get(layer.mask_storage_key)
            ).decode()
        edit_runner.run_edit(db, layer, mask_b64)
        return layer.status.value
    finally:
        db.close()
