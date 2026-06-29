from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, DbSession
from app.core.config import Environment, settings
from app.core.security import TokenType, create_token, decode_token
from app.schemas.auth import (
    AuthResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    Token,
)
from app.schemas.user import UserCreate, UserRead
from app.services import user_service
from app.services.user_service import EmailAlreadyExists

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(data: UserCreate, db: DbSession) -> AuthResponse:
    try:
        user = user_service.create_user(db, data)
    except EmailAlreadyExists as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from exc
    token = create_token(user.id, TokenType.ACCESS)
    return AuthResponse(access_token=token, user=UserRead.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> AuthResponse:
    # OAuth2 form uses `username`; we treat it as the email.
    user = user_service.authenticate(db, form.username, form.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    token = create_token(user.id, TokenType.ACCESS)
    return AuthResponse(access_token=token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post("/refresh", response_model=Token)
def refresh(current_user: CurrentUser) -> Token:
    return Token(access_token=create_token(current_user.id, TokenType.ACCESS))


@router.post("/password-reset/request", response_model=PasswordResetRequestResponse)
def request_password_reset(
    data: PasswordResetRequest, db: DbSession
) -> PasswordResetRequestResponse:
    user = user_service.get_by_email(db, data.email)
    # Always return success to avoid leaking which emails are registered.
    reset_token: str | None = None
    if user is not None:
        token = create_token(user.id, TokenType.RESET)
        # No email delivery in this FOSS stack yet — expose the token in dev
        # so the reset flow is fully testable. Never leaked in production.
        if settings.environment != Environment.PROD:
            reset_token = token
        # TODO(Phase 8+): send `token` via email in production.
    return PasswordResetRequestResponse(
        message="If that email is registered, a reset link has been sent.",
        reset_token=reset_token,
    )


@router.post("/password-reset/confirm", response_model=UserRead)
def confirm_password_reset(
    data: PasswordResetConfirm, db: DbSession
) -> UserRead:
    try:
        user_id = decode_token(data.token, expected_type=TokenType.RESET)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        ) from exc
    user = user_service.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    user = user_service.set_password(db, user, data.new_password)
    return UserRead.model_validate(user)
