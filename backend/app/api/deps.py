"""Shared FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import TokenType, decode_token
from app.db.models import User
from app.db.session import get_db
from app.services import user_service

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login", auto_error=True
)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = decode_token(token, expected_type=TokenType.ACCESS)
    except ValueError as exc:
        raise credentials_error from exc

    user = user_service.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise credentials_error
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_user_flexible(
    db: DbSession,
    token: Annotated[str | None, Query()] = None,
    header_token: Annotated[str | None, Depends(OAuth2PasswordBearer(
        tokenUrl=f"{settings.api_v1_prefix}/auth/login", auto_error=False
    ))] = None,
) -> User:
    """Auth for media endpoints: accepts a bearer header OR a `?token=` query.

    The query form lets <img>/<video> tags load protected media without custom
    headers. Note: putting tokens in URLs is a dev convenience — production
    should move to short-lived presigned URLs.
    """
    raw = header_token or token
    if not raw:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        user_id = decode_token(raw, expected_type=TokenType.ACCESS)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    user = user_service.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


FlexibleUser = Annotated[User, Depends(get_current_user_flexible)]
