"""Points calculation: floor(amount / usd_rate).

The legacy tier-based bonus is kept (deprecated) for reading historic
transactions, but new purchases always use USD-rate formula.
"""
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
from app.models import BonusTier


def calculate_points(amount: Decimal, usd_rate: Decimal) -> Decimal:
    """Return integer points = floor(amount / usd_rate).

    Returns Decimal for consistency with other money columns, but the
    value is always an integer (no fractional points by design).
    """
    if usd_rate is None or usd_rate <= 0:
        raise ValueError(f"invalid_usd_rate:{usd_rate}")
    if amount is None or amount < 0:
        raise ValueError(f"invalid_amount:{amount}")
    # amount in UZS / usd_rate (UZS per 1 USD) = USD equivalent
    # floor to integer points
    points = (Decimal(amount) / Decimal(usd_rate)).quantize(
        Decimal("1"), rounding=ROUND_FLOOR
    )
    return points


# ---------- Legacy (kept for historic-record reads) ----------
def calculate_bonus(
    amount: Decimal, tiers: list[BonusTier]
) -> tuple[Decimal, Decimal]:
    """DEPRECATED: tier-based calculation. Kept for completeness; new
    transactions must use calculate_points(amount, usd_rate) instead.
    """
    for tier in tiers:
        if amount < tier.min_amount:
            continue
        if tier.max_amount is not None and amount >= tier.max_amount:
            continue
        bonus = (amount * tier.percent / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return tier.percent, bonus
    raise ValueError(f"no_matching_tier_for_amount:{amount}")


def get_balance(db, user_id) -> Decimal:
    """Compute balance = SUM(delta) from bonus_ledger for a user."""
    from sqlalchemy import func
    from app.models import BonusLedger

    total = (
        db.query(func.coalesce(func.sum(BonusLedger.delta), 0))
        .filter(BonusLedger.user_id == user_id)
        .scalar()
    )
    return Decimal(total)
