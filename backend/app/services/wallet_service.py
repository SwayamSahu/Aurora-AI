"""Wallet + credit ledger. All balance mutations go through `credit`/`debit`
so `Wallet.balance_credits` never drifts from the `credit_transactions`
ledger, and every mutation happens inside the caller's DB transaction (no
`db.commit()` here) so multi-wallet operations like checkout stay atomic.

Concurrency: `get_wallet_locked` takes a `SELECT ... FOR UPDATE` row lock on
Postgres, preventing two concurrent requests from double-spending the same
balance. SQLite (used in tests) has no row-level locking — the clause is
silently dropped there, which is fine since SQLite already serializes
writes at the whole-database level.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import CreditTransaction, TransactionType, Wallet
from app.services.marketplace_errors import InsufficientCreditsError

# New users can list one item for free before buying a plan — keeps the
# marketplace from feeling fully paywalled to a first-time visitor.
FREE_LISTING_QUOTA = 1


def get_or_create_wallet(db: Session, user_id: str) -> Wallet:
    wallet = db.scalar(select(Wallet).where(Wallet.user_id == user_id))
    if wallet is not None:
        return wallet
    wallet = Wallet(user_id=user_id, listing_quota=FREE_LISTING_QUOTA)
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet


def get_wallet_locked(db: Session, user_id: str) -> Wallet:
    """Like `get_or_create_wallet`, but locks the row for the duration of the
    caller's transaction. Call this (not the unlocked variant) anywhere a
    balance is about to be read-then-mutated."""
    wallet = get_or_create_wallet(db, user_id)
    locked = db.scalar(select(Wallet).where(Wallet.id == wallet.id).with_for_update())
    assert locked is not None
    return locked


def credit(
    db: Session,
    wallet: Wallet,
    amount: int,
    tx_type: TransactionType,
    *,
    note: str | None = None,
    related_order_id: str | None = None,
) -> CreditTransaction:
    """Adds `amount` (positive) to the wallet and writes a ledger row.
    Does not commit — caller owns the transaction boundary."""
    if amount <= 0:
        raise ValueError("credit() amount must be positive; use debit() to remove.")
    wallet.balance_credits += amount
    tx = CreditTransaction(
        wallet_id=wallet.id,
        type=tx_type,
        amount=amount,
        balance_after=wallet.balance_credits,
        note=note,
        related_order_id=related_order_id,
    )
    db.add(tx)
    return tx


def debit(
    db: Session,
    wallet: Wallet,
    amount: int,
    tx_type: TransactionType,
    *,
    note: str | None = None,
    related_order_id: str | None = None,
) -> CreditTransaction:
    """Removes `amount` (positive) from the wallet. Raises
    `InsufficientCreditsError` if the wallet can't cover it. Does not
    commit — caller owns the transaction boundary."""
    if amount <= 0:
        raise ValueError("debit() amount must be positive.")
    if wallet.balance_credits < amount:
        raise InsufficientCreditsError(
            f"Wallet has {wallet.balance_credits} credits, needs {amount}."
        )
    wallet.balance_credits -= amount
    tx = CreditTransaction(
        wallet_id=wallet.id,
        type=tx_type,
        amount=-amount,
        balance_after=wallet.balance_credits,
        note=note,
        related_order_id=related_order_id,
    )
    db.add(tx)
    return tx


def list_transactions(
    db: Session, wallet_id: str, *, limit: int = 24, offset: int = 0
) -> tuple[list[CreditTransaction], int]:
    stmt = select(CreditTransaction).where(CreditTransaction.wallet_id == wallet_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = list(
        db.scalars(
            stmt.order_by(CreditTransaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    return items, total
