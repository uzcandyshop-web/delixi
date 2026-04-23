"""Bonus calculation: flat-tier lookup by purchase amount."""
from decimal import Decimal, ROUND_HALF_UP
from app.models import BonusTier


def calculate_bonus(
    amount: Decimal, tiers: list[BonusTier]
) -> tuple[Decimal, Decimal]:
    """Return (percent, bonus_amount) for a given purchase amount.

    Tiers are applied flat (not cumulative): entire amount gets the % of the
    matching tier. Tiers should be ordered by min_amount ascending.
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
