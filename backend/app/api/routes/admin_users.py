"""Admin user management: search/list users, view aggregated per-user
activity, and change role/active-status. Admin-only (not moderator) since
this touches account access, matching the money-adjacent routes in
`admin.py`."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AdminUser, DbSession
from app.db.models import UserRole
from app.schemas.admin import AdminUserDetail, AdminUserListResponse, AdminUserUpdate
from app.schemas.blog import BlogPostSummary
from app.schemas.listing import ListingSummary
from app.services import (
    audit_service,
    blog_service,
    gdpr_service,
    listing_service,
    order_service,
    user_service,
    wallet_service,
)

router = APIRouter(prefix="/admin/users", tags=["admin"])


@router.get("", response_model=AdminUserListResponse)
def list_users(
    admin: AdminUser,
    db: DbSession,
    q: Annotated[str | None, Query()] = None,
    role: Annotated[str | None, Query()] = None,
    is_active: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AdminUserListResponse:
    role_filter = UserRole(role) if role else None
    users, total = user_service.list_for_admin(
        db, q=q, role=role_filter, is_active=is_active, limit=limit, offset=offset
    )
    next_offset = offset + limit if offset + limit < total else None
    return AdminUserListResponse(items=users, total=total, next_offset=next_offset)


@router.get("/{user_id}", response_model=AdminUserDetail)
def get_user_detail(user_id: str, admin: AdminUser, db: DbSession) -> AdminUserDetail:
    user = user_service.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    wallet = wallet_service.get_or_create_wallet(db, user.id)
    posts = blog_service.list_for_author(db, user.id)
    listings = listing_service.list_for_seller(db, user.id)
    orders = order_service.list_for_buyer(db, user.id)
    sales = order_service.list_sales_for_seller(db, user.id)

    return AdminUserDetail(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        erased_at=user.erased_at,
        created_at=user.created_at,
        wallet_balance=wallet.balance_credits,
        listing_quota=wallet.listing_quota,
        post_count=len(posts),
        listing_count=len(listings),
        order_count=len(orders),
        sales_count=len(sales),
        recent_posts=[blog_service.to_read(BlogPostSummary, p) for p in posts[:5]],
        recent_listings=[
            listing_service.to_read(ListingSummary, listing) for listing in listings[:5]
        ],
    )


@router.patch("/{user_id}", response_model=AdminUserDetail)
def update_user(
    user_id: str, data: AdminUserUpdate, admin: AdminUser, db: DbSession
) -> AdminUserDetail:
    user = user_service.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    if data.role is not None:
        new_role = UserRole(data.role)
        if user.id == admin.id and new_role != UserRole.ADMIN:
            raise HTTPException(
                status_code=400, detail="You can't demote your own account."
            )
        if (
            user.role == UserRole.ADMIN
            and user.is_active
            and new_role != UserRole.ADMIN
            and user_service.count_active_admins(db) <= 1
        ):
            raise HTTPException(
                status_code=400,
                detail="Can't remove the last remaining active admin.",
            )
        user_service.set_role(db, user, new_role)
        audit_service.record(
            db,
            actor_id=admin.id,
            action="user.role_change",
            target_type="user",
            target_id=user.id,
            metadata={"role": new_role.value},
        )

    if data.is_active is not None:
        if user.id == admin.id and not data.is_active:
            raise HTTPException(
                status_code=400, detail="You can't suspend your own account."
            )
        if (
            user.role == UserRole.ADMIN
            and user.is_active
            and not data.is_active
            and user_service.count_active_admins(db) <= 1
        ):
            raise HTTPException(
                status_code=400,
                detail="Can't suspend the last remaining active admin.",
            )
        user_service.set_active(db, user, data.is_active)
        audit_service.record(
            db,
            actor_id=admin.id,
            action="user.suspend" if not data.is_active else "user.reactivate",
            target_type="user",
            target_id=user.id,
            metadata={"is_active": data.is_active},
        )

    return get_user_detail(user_id, admin, db)


@router.post("/{user_id}/erase", response_model=AdminUserDetail)
def erase_user(user_id: str, admin: AdminUser, db: DbSession) -> AdminUserDetail:
    """Admin-triggered GDPR erasure — for support-submitted deletion
    requests. Self-erasure goes through `POST /users/me/erase` instead."""
    user = user_service.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.id == admin.id:
        raise HTTPException(
            status_code=400, detail="Use account settings to erase your own account."
        )
    if (
        user.role == UserRole.ADMIN
        and user.is_active
        and user_service.count_active_admins(db) <= 1
    ):
        raise HTTPException(
            status_code=400, detail="Can't erase the last remaining active admin."
        )

    gdpr_service.anonymize_user(db, user)
    audit_service.record(
        db,
        actor_id=admin.id,
        action="user.erase",
        target_type="user",
        target_id=user.id,
        metadata={},
    )
    return get_user_detail(user_id, admin, db)
