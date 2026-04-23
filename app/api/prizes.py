"""Prize catalog and customer redemption requests."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.deps import current_user, require_customer
from app.models import User, Prize, Redemption
from app.schemas import PrizeOut, RedemptionCreate, RedemptionOut
from app.services.redemptions import request_redemption, RedemptionError

router = APIRouter(prefix="/api/v1", tags=["prizes"])


@router.get("/prizes", response_model=list[PrizeOut])
def list_prizes(db: Session = Depends(get_db)):
    rows = (
        db.query(Prize)
        .filter(Prize.is_active.is_(True), Prize.stock > 0)
        .order_by(Prize.cost_bonus)
        .all()
    )
    return [
        PrizeOut(
            id=p.id,
            name=p.name,
            description=p.description,
            cost_bonus=p.cost_bonus,
            stock=p.stock,
            image_url=p.image_url,
        )
        for p in rows
    ]


@router.post("/redemptions", response_model=RedemptionOut)
def create_redemption(
    body: RedemptionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_customer),
):
    try:
        red = request_redemption(db, user, body.prize_id)
    except RedemptionError as e:
        status_map = {
            "prize_not_found": 404,
            "out_of_stock": 409,
            "insufficient_balance": 400,
        }
        raise HTTPException(status_map.get(e.code, 400), detail={"error": e.code, **e.extra})

    return RedemptionOut(
        id=red.id,
        prize_id=red.prize_id,
        prize_name=red.prize.name,
        cost_bonus=red.cost_bonus,
        status=red.status,
        requested_at=red.requested_at,
        resolved_at=red.resolved_at,
        note=red.note,
    )


@router.get("/redemptions/me", response_model=list[RedemptionOut])
def my_redemptions(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Redemption)
        .filter(Redemption.user_id == user.id)
        .order_by(Redemption.requested_at.desc())
        .limit(50)
        .all()
    )
    return [
        RedemptionOut(
            id=r.id,
            prize_id=r.prize_id,
            prize_name=r.prize.name,
            cost_bonus=r.cost_bonus,
            status=r.status,
            requested_at=r.requested_at,
            resolved_at=r.resolved_at,
            note=r.note,
        )
        for r in rows
    ]
