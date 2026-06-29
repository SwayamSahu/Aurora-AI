"""Export orchestration: timeline document → MP4 stored as a derived asset.

Called from the Celery export task via `run_export(db, job)`.
Downloads each referenced asset from storage to temp files, builds the render
plan, invokes the FFmpeg pipeline, uploads the result, and records the output
asset on the job.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models import Asset, Job, Project
from app.db.models.asset import AssetKind, AssetSource
from app.db.models.job import JobStatus
from app.media.ffmpeg_pipeline import RenderParams, build_render_plan, render_to_mp4
from app.services import asset_service, job_service, timeline_service
from app.storage import get_storage

_SUPPORTED_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".wav", ".mp3", ".ogg", ".m4a", ".png", ".jpg", ".jpeg"}


def _ext_for_content_type(ct: str) -> str:
    ct = ct.lower().split(";")[0].strip()
    _MAP = {
        "video/mp4": ".mp4", "video/quicktime": ".mov", "video/webm": ".webm",
        "video/x-matroska": ".mkv", "video/avi": ".avi",
        "audio/wav": ".wav", "audio/mpeg": ".mp3", "audio/mp4": ".m4a",
        "audio/ogg": ".ogg",
        "image/png": ".png", "image/jpeg": ".jpg", "image/gif": ".gif",
        "image/webp": ".webp",
    }
    return _MAP.get(ct, ".bin")


def run_export(db: Session, job: Job) -> Job:
    """Compile the project's current timeline to an MP4 and attach it to job.

    Never raises — failures are captured on job.error / status=FAILED.
    """
    project = db.get(Project, job.project_id)
    if project is None:
        job_service.mark_failed(db, job, "Project not found.")
        return job

    job_service.set_progress(db, job, 0.05, status=JobStatus.RUNNING)

    def progress(fraction: float, message: str = "") -> None:
        job_service.set_progress(db, job, fraction)

    params_raw = job.params or {}
    render_params = RenderParams(
        width=int(params_raw.get("width", 1280)),
        height=int(params_raw.get("height", 720)),
        fps=int(params_raw.get("fps", 24)),
        crf=int(params_raw.get("crf", 23)),
        fade_duration=float(params_raw.get("fade_duration", 0.5)),
    )

    # --- Load the timeline document ---
    try:
        tv = timeline_service.get_current(db, project.id)
        document = tv.document if isinstance(tv.document, dict) else {}
    except Exception as exc:  # noqa: BLE001
        job_service.mark_failed(db, job, f"Could not load timeline: {exc}")
        return job

    # --- Resolve all referenced asset IDs ---
    asset_ids: set[str] = set()
    for track in document.get("tracks", []):
        for clip in track.get("clips", []):
            aid = clip.get("asset_id")
            if aid:
                asset_ids.add(aid)

    progress(0.1, "downloading assets")

    # --- Download each asset to a temp file ---
    tmpdir = tempfile.mkdtemp(prefix="aurora_export_")
    asset_paths: dict[str, str] = {}
    storage = get_storage()

    try:
        for aid in asset_ids:
            asset: Asset | None = db.get(Asset, aid)
            if asset is None or asset.project_id != project.id:
                continue
            ext = _ext_for_content_type(asset.content_type)
            path = os.path.join(tmpdir, f"{aid}{ext}")
            try:
                data = storage.get(asset.storage_key)
                Path(path).write_bytes(data)
                asset_paths[aid] = path
            except Exception:  # noqa: BLE001
                # Skip unavailable assets; the pipeline will gap-fill.
                pass

        progress(0.2, "planning render")
        plan = build_render_plan(document, asset_paths, render_params)

        # --- Render ---
        output_path = os.path.join(tmpdir, "export.mp4")
        render_to_mp4(plan, output_path, progress=lambda f, m="": progress(0.2 + f * 0.7, m))

        # --- Upload the result ---
        progress(0.95, "uploading")
        mp4_bytes = Path(output_path).read_bytes()
        export_asset = asset_service.create_from_upload(
            db,
            project,
            filename=f"{project.name}_export.mp4",
            data=mp4_bytes,
            content_type="video/mp4",
            source=AssetSource.DERIVED,
            kind=AssetKind.VIDEO,
        )
        job_service.mark_succeeded(db, job, export_asset.id)

    except Exception as exc:  # noqa: BLE001
        job_service.mark_failed(db, job, str(exc)[:2000])
    finally:
        # Clean up temp files.
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)

    return job
