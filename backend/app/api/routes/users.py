from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import CurrentUser, DbSession
from app.core.security import verify_password
from app.schemas.user import PasswordChange, UserRead, UserUpdate
from app.services import user_service

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
