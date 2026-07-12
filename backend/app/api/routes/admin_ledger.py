"""Global credit-ledger search across every wallet — admin-only, since it
exposes every user's financial history in one place."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import AdminUser, DbSession
from app.db.models import TransactionType
from app.schemas.admin import LedgerEntryRead, LedgerEntryUser, LedgerSearchResponse
from app.services import wallet_service

router = APIRouter(prefix="/admin/ledger", tags=["admin"])


@router.get("", response_model=LedgerSearchResponse)
def search_ledger(
    admin: AdminUser,
    db: DbSession,
    q: Annotated[str | None, Query()] = None,
    type: Annotated[str | None, Query()] = None,
    user_id: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> LedgerSearchResponse:
    tx_type = TransactionType(type) if type else None
    rows, total = wallet_service.search_transactions(
        db, q=q, tx_type=tx_type, user_id=user_id, limit=limit, offset=offset
    )
    items = [
        LedgerEntryRead(
            id=tx.id,
            wallet_id=tx.wallet_id,
            user=LedgerEntryUser(id=user.id, email=user.email, full_name=user.full_name),
            type=tx.type.value,
            amount=tx.amount,
            balance_after=tx.balance_after,
            note=tx.note,
            related_order_id=tx.related_order_id,
            created_at=tx.created_at,
        )
        for tx, user in rows
    ]
    next_offset = offset + limit if offset + limit < total else None
    return LedgerSearchResponse(items=items, total=total, next_offset=next_offset)
