"""User-facing read endpoints: /me, /me/history, /regions."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.deps import current_user
from app.models import User, Region, Transaction
from app.schemas import MeResponse, HistoryItem, RegionOut
from app.services.bonus import get_balance

router = APIRouter(prefix="/api/v1", tags=["user"])


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return MeResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role,
        region=user.region.name_ru,
        balance=get_balance(db, user.id),
    )


@router.get("/me/history", response_model=list[HistoryItem])
def my_history(
    limit: int = 20,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    limit = min(max(limit, 1), 100)
    rows = (
        db.query(Transaction)
        .filter(Transaction.customer_id == user.id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        HistoryItem(
            id=r.id,
            amount=r.amount,
            bonus_amount=r.bonus_amount,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.get("/regions", response_model=list[RegionOut])
def list_regions(db: Session = Depends(get_db)):
    rows = db.query(Region).filter(Region.is_active.is_(True)).order_by(Region.name_ru).all()
    return [RegionOut(id=r.id, code=r.code, name_ru=r.name_ru, name_uz=r.name_uz) for r in rows]
