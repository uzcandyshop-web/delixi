"""Admin endpoints: tiers, redemptions, reports."""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db import get_db
from app.deps import require_admin
from app.models import User, BonusTier, Redemption, Transaction, Region
from app.schemas import TiersUpdate, ResolveRedemption, RedemptionOut
from app.services.redemptions import (
    approve_redemption, reject_redemption, RedemptionError,
)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/tiers")
def replace_tiers(
    body: TiersUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Replace all tiers atomically. Simple for MVP."""
    # Validation: ranges shouldn't overlap
    sorted_tiers = sorted(body.tiers, key=lambda t: t.min_amount)
    for i, t in enumerate(sorted_tiers[:-1]):
        next_t = sorted_tiers[i + 1]
        if t.max_amount is None or t.max_amount > next_t.min_amount:
            raise HTTPException(400, detail={"error": "overlapping_tiers"})

    db.query(BonusTier).delete()
    for t in sorted_tiers:
        db.add(BonusTier(
            min_amount=t.min_amount,
            max_amount=t.max_amount,
            percent=t.percent,
            created_by=admin.id,
        ))
    db.commit()
    return {"ok": True, "count": len(sorted_tiers)}


@router.get("/redemptions/pending", response_model=list[RedemptionOut])
def pending_redemptions(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    rows = (
        db.query(Redemption)
        .filter(Redemption.status == "pending")
        .order_by(Redemption.requested_at)
        .all()
    )
    return [
        RedemptionOut(
            id=r.id, prize_id=r.prize_id, prize_name=r.prize.name,
            cost_bonus=r.cost_bonus, status=r.status,
            requested_at=r.requested_at, resolved_at=r.resolved_at,
            note=r.note,
        )
        for r in rows
    ]


@router.post("/redemptions/{redemption_id}/resolve")
def resolve(
    redemption_id: str,
    body: ResolveRedemption,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        if body.action == "approve":
            red = approve_redemption(db, admin, redemption_id)
        elif body.action == "reject":
            red = reject_redemption(db, admin, redemption_id, body.note)
        else:
            raise HTTPException(400, detail={"error": "bad_action"})
    except RedemptionError as e:
        raise HTTPException(400, detail={"error": e.code, **e.extra})
    return {"ok": True, "status": red.status}


@router.get("/reports/turnover")
def turnover(
    days: int = 7,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Turnover by region for the last N days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        db.query(
            Region.code,
            Region.name_ru,
            func.count(Transaction.id).label("tx_count"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            func.coalesce(func.sum(Transaction.bonus_amount), 0).label("total_bonus"),
        )
        .join(Transaction, Transaction.region_id == Region.id)
        .filter(Transaction.created_at >= since)
        .group_by(Region.id)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )
    return {
        "period_days": days,
        "regions": [
            {
                "code": r.code,
                "name": r.name_ru,
                "tx_count": r.tx_count,
                "total_amount": str(r.total_amount),
                "total_bonus": str(r.total_bonus),
            }
            for r in rows
        ],
    }
