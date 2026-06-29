"""WebSocket job-progress streaming.

Backend-agnostic: it polls the Job row and pushes changes. This works whether
the job ran inline (eager) or is being updated by a separate Celery worker —
no Redis pub/sub required. Auth is via a `?token=` query param (WebSockets
can't carry an Authorization header from the browser easily).
"""

from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.security import TokenType, decode_token
from app.db.models.job import JobStatus
from app.db.session import get_db
from app.schemas.job import JobProgressEvent
from app.services import job_service

router = APIRouter()

TERMINAL = {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED}
POLL_SECONDS = 0.4
MAX_ITERATIONS = 1800  # ~12 minutes safety cap


@router.websocket("/ws/jobs/{job_id}")
async def job_progress(
    websocket: WebSocket,
    job_id: str,
    token: Annotated[str | None, Query()] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> None:
    # Authenticate before accepting.
    if not token:
        await websocket.close(code=4401)
        return
    try:
        user_id = decode_token(token, expected_type=TokenType.ACCESS)
    except ValueError:
        await websocket.close(code=4401)
        return

    job = job_service.get_for_owner(db, user_id, job_id)
    if job is None:
        await websocket.close(code=4404)
        return

    await websocket.accept()
    last_signature: tuple | None = None
    try:
        for _ in range(MAX_ITERATIONS):
            # Re-read fresh state (worker may update it in another session).
            db.expire_all()
            job = job_service.get_for_owner(db, user_id, job_id)
            if job is None:
                break

            signature = (job.status, round(job.progress, 3), job.result_asset_id)
            if signature != last_signature:
                last_signature = signature
                event = JobProgressEvent(
                    id=job.id,
                    status=job.status,
                    progress=job.progress,
                    error=job.error,
                    result_asset_id=job.result_asset_id,
                )
                await websocket.send_json(event.model_dump(mode="json"))

            if job.status in TERMINAL:
                break
            await asyncio.sleep(POLL_SECONDS)
    except WebSocketDisconnect:
        return
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass
