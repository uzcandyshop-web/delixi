"""Prize redemption flow: request → approve (list-debit) / reject."""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import (
    User, Prize, Redemption, RedemptionStatus, BonusLedger, LedgerReason,
)
from app.services.bonus import get_balance


class RedemptionError(Exception):
    def __init__(self, code: str, **extra):
        self.code = code
        self.extra = extra
        super().__init__(code)


def request_redemption(db: Session, user: User, prize_id) -> Redemption:
    """Customer requests a prize. Creates pending redemption; no debit yet."""
    prize = db.get(Prize, prize_id)
    if not prize or not prize.is_active:
        raise RedemptionError("prize_not_found")
    if prize.stock <= 0:
        raise RedemptionError("out_of_stock")

    balance = get_balance(db, user.id)
    if balance < prize.cost_bonus:
        raise RedemptionError(
            "insufficient_balance",
            balance=str(balance),
            required=str(prize.cost_bonus),
        )

    red = Redemption(
        user_id=user.id,
        prize_id=prize.id,
        cost_bonus=prize.cost_bonus,
        status=RedemptionStatus.PENDING.value,
    )
    db.add(red)
    db.commit()
    db.refresh(red)
    return red


def approve_redemption(db: Session, admin: User, redemption_id) -> Redemption:
    """Admin approves — debit bonuses, decrement stock."""
    red = db.get(Redemption, redemption_id)
    if not red:
        raise RedemptionError("redemption_not_found")
    if red.status != RedemptionStatus.PENDING.value:
        raise RedemptionError("not_pending", status=red.status)

    prize = db.get(Prize, red.prize_id)
    if prize.stock <= 0:
        raise RedemptionError("out_of_stock")

    balance = get_balance(db, red.user_id)
    if balance < red.cost_bonus:
        raise RedemptionError("balance_changed", balance=str(balance))

    prize.stock -= 1
    red.status = RedemptionStatus.APPROVED.value
    red.resolved_at = datetime.now(timezone.utc)
    red.resolved_by = admin.id

    db.add(
        BonusLedger(
            user_id=red.user_id,
            delta=-red.cost_bonus,
            reason=LedgerReason.REDEEM.value,
            redemption_id=red.id,
        )
    )
    db.commit()
    db.refresh(red)
    return red


def reject_redemption(
    db: Session, admin: User, redemption_id, note: str | None = None
) -> Redemption:
    red = db.get(Redemption, redemption_id)
    if not red:
        raise RedemptionError("redemption_not_found")
    if red.status != RedemptionStatus.PENDING.value:
        raise RedemptionError("not_pending", status=red.status)

    red.status = RedemptionStatus.REJECTED.value
    red.resolved_at = datetime.now(timezone.utc)
    red.resolved_by = admin.id
    red.note = note
    db.commit()
    db.refresh(red)
    return red
