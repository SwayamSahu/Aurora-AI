from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import CurrentUser, DbSession
from app.core.security import verify_password
from app.schemas.user import AccountErasureRequest, PasswordChange, UserRead, UserUpdate
from app.services import gdpr_service, user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.patch("/me", response_model=UserRead)
def update_me(
    data: UserUpdate, current_user: CurrentUser, db: DbSession
) -> UserRead:
    user = user_service.update_user(db, current_user, data)
    return UserRead.model_validate(user)


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    data: PasswordChange, current_user: CurrentUser, db: DbSession
) -> Response:
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )
    user_service.set_password(db, current_user, data.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/export")
def export_my_data(current_user: CurrentUser, db: DbSession) -> dict:
    """GDPR Art. 20 data portability — everything the platform holds about
    the caller, as one downloadable JSON document."""
    return gdpr_service.export_user_data(db, current_user)


@router.post("/me/erase", status_code=status.HTTP_204_NO_CONTENT)
def erase_my_account(
    data: AccountErasureRequest, current_user: CurrentUser, db: DbSession
) -> Response:
    """GDPR Art. 17 right to erasure — scrubs PII and deactivates the
    account. Password-confirmed since it's irreversible."""
    if not verify_password(data.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect.",
        )
    gdpr_service.anonymize_user(db, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
