"""Asset persistence: bytes go to storage, metadata to the database."""

from __future__ import annotations

import uuid
from pathlib import PurePosixPath

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Asset, Project
from app.db.models.asset import AssetKind, AssetSource
from app.storage import get_storage


def kind_from_content_type(content_type: str) -> AssetKind:
    ct = (content_type or "").lower()
    if ct.startswith("video/"):
        return AssetKind.VIDEO
    if ct.startswith("image/"):
        return AssetKind.IMAGE
    if ct.startswith("audio/"):
        return AssetKind.AUDIO
    if "subrip" in ct or ct in {"text/vtt", "application/x-subrip", "text/plain"}:
        return AssetKind.SUBTITLES
    return AssetKind.VIDEO


def content_url(asset_id: str) -> str:
    return f"{settings.api_v1_prefix}/assets/{asset_id}/content"


def _safe_name(name: str) -> str:
    return PurePosixPath(name).name.replace(" ", "_") or "file"


def create_from_upload(
    db: Session,
    project: Project,
    *,
    filename: str,
    data: bytes,
    content_type: str,
    source: AssetSource = AssetSource.UPLOADED,
    kind: AssetKind | None = None,
    duration_seconds: float | None = None,
    width: int | None = None,
    height: int | None = None,
) -> Asset:
    asset_id = str(uuid.uuid4())
    safe = _safe_name(filename)
    key = f"projects/{project.id}/{asset_id}/{safe}"
    get_storage().put(key, data, content_type)

    asset = Asset(
        id=asset_id,
        project_id=project.id,
        name=filename,
        kind=kind or kind_from_content_type(content_type),
        source=source,
        storage_key=key,
        content_type=content_type,
        duration_seconds=duration_seconds,
        width=width,
        height=height,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def list_for_project(
    db: Session, project_id: str, *, kind: AssetKind | None = None
) -> list[Asset]:
    stmt = select(Asset).where(Asset.project_id == project_id)
    if kind is not None:
        stmt = stmt.where(Asset.kind == kind)
    stmt = stmt.order_by(Asset.created_at.desc())
    return list(db.scalars(stmt).all())


def get_for_owner(db: Session, owner_id: str, asset_id: str) -> Asset | None:
    return db.scalar(
        select(Asset)
        .join(Project, Project.id == Asset.project_id)
        .where(Asset.id == asset_id, Project.owner_id == owner_id)
    )


def delete(db: Session, asset: Asset) -> None:
    get_storage().delete(asset.storage_key)
    db.delete(asset)
    db.commit()
