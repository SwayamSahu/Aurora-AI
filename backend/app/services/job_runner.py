"""Job orchestration.

Pure function `run_generation(db, job)` that drives a generator from the
registry, streams progress onto the Job row, and persists the result as a
generated Asset. Used both inline (eager/dev/tests) and from the Celery worker.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.db.models import Asset, Job, Project
from app.db.models.asset import AssetKind, AssetSource
from app.db.models.job import JobStatus, JobType
from app.generators.base import (
    GeneratedMedia,
    ImageGenParams,
    MusicGenParams,
    VideoGenParams,
    VoiceGenParams,
)
from app.generators.model_catalog import clamp_video_params, get_model
from app.generators.registry import (
    get_image_generator,
    get_music_generator,
    get_transcriber,
    get_video_generator,
    get_voice_generator,
)
from app.media.video_frames import extract_first_frame
from app.services import asset_service, content_safety_service, job_service
from app.storage import get_storage

logger = logging.getLogger(__name__)

_KIND_MAP = {
    "video": AssetKind.VIDEO,
    "image": AssetKind.IMAGE,
    "audio": AssetKind.AUDIO,
    "subtitles": AssetKind.SUBTITLES,
}

# Generated media kinds the automated content-safety scan screens. Audio/
# subtitle outputs (TTS, music, transcription) aren't image-classifiable and
# are out of scope here.
_SAFETY_SCANNED_JOB_TYPES = {JobType.GENERATE_VIDEO, JobType.GENERATE_IMAGE}


def _scan_generated_asset(db: Session, job: Job, asset: Asset, media: GeneratedMedia) -> None:
    """Runs the automated content-safety scan on a freshly generated asset.
    Never raises — a scan failure (e.g. a corrupt frame extraction) must not
    fail an otherwise-successful generation; it's logged and skipped."""
    if job.type not in _SAFETY_SCANNED_JOB_TYPES:
        return
    try:
        if media.kind == "image":
            content_safety_service.scan_and_flag(
                db, asset, image_bytes=media.data, target_type="asset"
            )
        elif media.kind == "video":
            frame = extract_first_frame(media.data)
            content_safety_service.scan_and_flag(
                db,
                asset,
                image_bytes=frame,
                target_type="asset",
                content_type="image/png",
            )
    except Exception:  # noqa: BLE001 — moderation scan is best-effort
        logger.warning(
            "Content-safety scan failed for asset %s (job %s)", asset.id, job.id,
            exc_info=True,
        )


def _generate(job: Job, progress) -> GeneratedMedia:
    p = job.params or {}
    if job.type == JobType.GENERATE_VIDEO:
        duration = float(p.get("duration_seconds", 4.0))
        width = int(p.get("width", 768))
        height = int(p.get("height", 512))
        # Clamp the request to the chosen model's capability envelope so it's
        # valid whichever backend serves it (see model_catalog).
        spec = get_model(p.get("model"))
        if spec is not None:
            duration, width, height = clamp_video_params(
                spec, duration, width, height
            )
        params = VideoGenParams(
            prompt=p.get("prompt", ""),
            negative_prompt=p.get("negative_prompt"),
            duration_seconds=duration,
            width=width,
            height=height,
            fps=int(p.get("fps", 24)),
            seed=p.get("seed"),
            model=p.get("model"),
        )
        return get_video_generator().generate(params, progress)

    if job.type == JobType.GENERATE_IMAGE:
        params = ImageGenParams(
            prompt=p.get("prompt", ""),
            negative_prompt=p.get("negative_prompt"),
            width=int(p.get("width", 1024)),
            height=int(p.get("height", 1024)),
            seed=p.get("seed"),
            model=p.get("model"),
        )
        return get_image_generator().generate(params, progress)

    if job.type == JobType.TTS:
        params = VoiceGenParams(
            text=p.get("text", ""),
            voice=p.get("voice", "default"),
            speed=float(p.get("speed", 1.0)),
        )
        return get_voice_generator().generate(params, progress)

    if job.type == JobType.MUSIC:
        params = MusicGenParams(
            prompt=p.get("prompt", ""),
            duration_seconds=float(p.get("duration_seconds", 10.0)),
        )
        return get_music_generator().generate(params, progress)

    raise ValueError(f"Unsupported job type for generation: {job.type.value}")


def _run_transcribe(db: Session, job: Job, project: Project, progress) -> None:
    asset_id = (job.params or {}).get("asset_id")
    source = db.get(Asset, asset_id) if asset_id else None
    if source is None or source.project_id != project.id:
        job_service.mark_failed(db, job, "Source asset not found.")
        return

    data = get_storage().get(source.storage_key)
    result = get_transcriber().transcribe(data, source.content_type, progress)
    asset = asset_service.create_from_upload(
        db,
        project,
        filename=f"{source.name}.srt",
        data=result.srt.encode("utf-8"),
        content_type="application/x-subrip",
        source=AssetSource.DERIVED,
        kind=AssetKind.SUBTITLES,
    )
    job_service.mark_succeeded(db, job, asset.id)


def run_generation(db: Session, job: Job) -> Job:
    """Run the job to completion, recording outcome on the Job row.

    Never raises: failures are captured on `job.error` / status=FAILED so both
    the inline and Celery paths leave the job in a terminal state.
    """
    project = db.get(Project, job.project_id)
    if project is None:
        # No refund here: `Job.project_id` is ON DELETE CASCADE, so deleting a
        # project also deletes its jobs — a charged job can't reach this branch
        # with a missing project, and without the project there's no owner to
        # refund to anyway. The refund path that matters is the generation
        # failure below, where the project (and its wallet) still exist.
        job_service.mark_failed(db, job, "Project no longer exists.")
        return job

    job_service.set_progress(db, job, 0.0, status=JobStatus.RUNNING)

    def progress(fraction: float, message: str | None = None) -> None:
        job_service.set_progress(db, job, fraction)

    try:
        if job.type == JobType.TRANSCRIBE:
            _run_transcribe(db, job, project, progress)
            return job

        media = _generate(job, progress)
        asset = asset_service.create_from_upload(
            db,
            project,
            filename=media.suggested_filename,
            data=media.data,
            content_type=media.content_type,
            source=AssetSource.GENERATED,
            kind=_KIND_MAP.get(media.kind),
            duration_seconds=media.duration_seconds,
            width=media.width,
            height=media.height,
        )
        _scan_generated_asset(db, job, asset, media)
        job_service.mark_succeeded(db, job, asset.id)
    except Exception as exc:  # noqa: BLE001 — record any failure on the job
        job_service.refund_credits(db, job)
        job_service.mark_failed(db, job, str(exc))
    return job
