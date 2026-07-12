"""User persistence and authentication logic."""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.db.models import User, UserRole
from app.schemas.user import UserCreate, UserUpdate


class EmailAlreadyExists(Exception):
    pass


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def get_by_id(db: Session, user_id: str) -> User | None:
    return db.get(User, user_id)


def create_user(db: Session, data: UserCreate) -> User:
    if get_by_email(db, data.email):
        raise EmailAlreadyExists(data.email)
    user = User(
        email=data.email.lower(),
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        preferences={},
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = get_by_email(db, email)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def update_user(db: Session, user: User, data: UserUpdate) -> User:
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.preferences is not None:
        # Merge rather than replace so partial updates are safe.
        user.preferences = {**(user.preferences or {}), **data.preferences}
    db.commit()
    db.refresh(user)
    return user


def set_password(db: Session, user: User, new_password: str) -> User:
    user.hashed_password = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user


def list_for_admin(
    db: Session,
    *,
    q: str | None = None,
    role: UserRole | None = None,
    is_active: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[User], int]:
    stmt = select(User)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(func.lower(User.email).like(like), func.lower(User.full_name).like(like))
        )
    if role is not None:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)
    items = list(db.scalars(stmt).all())
    return items, total


def count_active_admins(db: Session) -> int:
    return (
        db.scalar(
            select(func.count()).where(
                User.role == UserRole.ADMIN, User.is_active.is_(True)
            )
        )
        or 0
    )


def set_role(db: Session, user: User, role: UserRole) -> User:
    user.role = role
    db.commit()
    db.refresh(user)
    return user


def set_active(db: Session, user: User, is_active: bool) -> User:
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user
