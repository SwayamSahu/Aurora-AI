"""Project persistence, scoped to the owning user."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Asset, Project
from app.schemas.project import ProjectCreate, ProjectUpdate


def create(db: Session, owner_id: str, data: ProjectCreate) -> Project:
    project = Project(
        owner_id=owner_id, name=data.name, description=data.description
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get(db: Session, owner_id: str, project_id: str) -> Project | None:
    return db.scalar(
        select(Project).where(
            Project.id == project_id, Project.owner_id == owner_id
        )
    )


def list_for_owner(
    db: Session,
    owner_id: str,
    *,
    search: str | None = None,
    sort: str = "recent",
) -> list[tuple[Project, int]]:
    """Return (project, asset_count) tuples for the owner."""
    stmt = (
        select(Project, func.count(Asset.id))
        .outerjoin(Asset, Asset.project_id == Project.id)
        .where(Project.owner_id == owner_id)
        .group_by(Project.id)
    )
    if search:
        stmt = stmt.where(Project.name.ilike(f"%{search}%"))

    if sort == "name":
        stmt = stmt.order_by(Project.name.asc())
    elif sort == "oldest":
        stmt = stmt.order_by(Project.created_at.asc())
    else:  # recent
        stmt = stmt.order_by(Project.updated_at.desc())

    return [(row[0], row[1]) for row in db.execute(stmt).all()]


def update(db: Session, project: Project, data: ProjectUpdate) -> Project:
    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    db.commit()
    db.refresh(project)
    return project


def delete(db: Session, project: Project) -> None:
    db.delete(project)
    db.commit()


def duplicate(db: Session, project: Project) -> Project:
    """Shallow duplicate: copies the project shell (not assets) for now."""
    copy = Project(
        owner_id=project.owner_id,
        name=f"{project.name} (copy)",
        description=project.description,
    )
    db.add(copy)
    db.commit()
    db.refresh(copy)
    return copy


def asset_count(db: Session, project_id: str) -> int:
    return (
        db.scalar(
            select(func.count(Asset.id)).where(Asset.project_id == project_id)
        )
        or 0
    )
