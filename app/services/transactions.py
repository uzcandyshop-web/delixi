"""Transaction creation: QR decode, region check, tier calc, ledger write."""
from decimal import Decimal
from sqlalchemy.orm import Session
from app.core.qr import qr_decode
from app.models import User, BonusTier, Transaction, BonusLedger, LedgerReason, UserRole
from app.services.bonus import calculate_bonus, get_balance


class TxError(Exception):
    """Domain error with a machine-readable code."""
    def __init__(self, code: str, **extra):
        self.code = code
        self.extra = extra
        super().__init__(code)


def create_transaction(
    db: Session,
    seller: User,
    qr_token: str,
    amount: Decimal,
    idempotency_key: str,
) -> tuple[Transaction, bool, Decimal]:
    """Create a purchase transaction and accrue bonus.

    Returns (transaction, replayed, balance_after). Commits on success.
    """
    # 1. Idempotency check
    existing = (
        db.query(Transaction).filter_by(idempotency_key=idempotency_key).first()
    )
    if existing:
        balance = get_balance(db, existing.customer_id)
        return existing, True, balance

    # 2. Seller validity
    if seller.role != UserRole.SELLER.value or not seller.is_active:
        raise TxError("seller_inactive")

    # 3. Decode QR
    try:
        customer_id = qr_decode(qr_token)
    except ValueError as e:
        raise TxError("invalid_qr", detail=str(e))

    customer = db.get(User, customer_id)
    if not customer or customer.role != UserRole.CUSTOMER.value or not customer.is_active:
        raise TxError("customer_not_found")

    # 4. Region isolation
    if customer.region_id != seller.region_id:
        raise TxError(
            "region_mismatch",
            customer_region=customer.region.name_ru,
            seller_region=seller.region.name_ru,
        )

    # 5. Amount check
    if amount <= 0:
        raise TxError("bad_amount")

    # 6. Tier lookup
    tiers = db.query(BonusTier).order_by(BonusTier.min_amount).all()
    if not tiers:
        raise TxError("no_tiers_configured")
    try:
        percent, bonus = calculate_bonus(amount, tiers)
    except ValueError:
        raise TxError("no_matching_tier", amount=str(amount))

    # 7. Write in one DB transaction
    tx = Transaction(
        customer_id=customer.id,
        seller_id=seller.id,
        region_id=seller.region_id,
        amount=amount,
        bonus_percent=percent,
        bonus_amount=bonus,
        idempotency_key=idempotency_key,
    )
    db.add(tx)
    db.flush()

    db.add(
        BonusLedger(
            user_id=customer.id,
            delta=bonus,
            reason=LedgerReason.PURCHASE.value,
            tx_id=tx.id,
        )
    )
    db.commit()
    db.refresh(tx)

    balance = get_balance(db, customer.id)
    return tx, False, balance
