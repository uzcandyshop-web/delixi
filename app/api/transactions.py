"""POST /transactions — the main business endpoint."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.deps import require_seller
from app.models import User
from app.schemas import TxCreate, TxResult, TxCustomerInfo
from app.services.transactions import create_transaction, TxError

router = APIRouter(prefix="/api/v1", tags=["transactions"])


@router.post("/transactions", response_model=TxResult)
async def create_tx(
    body: TxCreate,
    db: Session = Depends(get_db),
    seller: User = Depends(require_seller),
):
    try:
        tx, replayed, balance = create_transaction(
            db=db,
            seller=seller,
            qr_token=body.qr_token,
            amount=body.amount,
            idempotency_key=body.idempotency_key,
        )
    except TxError as e:
        status_map = {
            "seller_inactive": 403,
            "invalid_qr": 400,
            "customer_not_found": 404,
            "region_mismatch": 403,
            "bad_amount": 400,
            "no_tiers_configured": 500,
            "no_matching_tier": 400,
        }
        raise HTTPException(status_map.get(e.code, 400), detail={"error": e.code, **e.extra})

    # Fire-and-forget customer notification (no blocking on Telegram API)
    import asyncio
    from app.bot.notify import notify_purchase
    asyncio.create_task(
        notify_purchase(
            telegram_id=tx.customer.telegram_id,
            amount=tx.amount,
            bonus=tx.bonus_amount,
            balance=balance,
        )
    )

    return TxResult(
        transaction_id=tx.id,
        customer=TxCustomerInfo(
            name=tx.customer.full_name,
            region=tx.customer.region.name_ru,
        ),
        amount=tx.amount,
        bonus_percent=tx.bonus_percent,
        bonus_amount=tx.bonus_amount,
        balance_after=balance,
        replayed=replayed,
    )
