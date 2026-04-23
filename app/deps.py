"""FastAPI dependencies: DB session, Telegram auth, role gates."""
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.core.tg_auth import verify_init_data
from app.models import User, UserRole


def current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated Telegram user from the Authorization header.

    Expected format: `Authorization: tg <init_data>`
    """
    if not authorization or not authorization.startswith("tg "):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="missing_tg_auth"
        )

    init_data = authorization[3:].strip()
    try:
        parsed = verify_init_data(init_data)
    except ValueError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(e))

    tg_user = parsed.get("user")
    if not tg_user or "id" not in tg_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="no_user_in_init")

    user = (
        db.query(User)
        .filter(User.telegram_id == int(tg_user["id"]), User.deleted_at.is_(None))
        .first()
    )
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="user_not_registered")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="user_inactive")
    return user


def require_seller(user: User = Depends(current_user)) -> User:
    if user.role != UserRole.SELLER.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="seller_required")
    return user


def require_customer(user: User = Depends(current_user)) -> User:
    if user.role != UserRole.CUSTOMER.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="customer_required")
    return user


def require_admin(user: User = Depends(current_user)) -> User:
    if user.role != UserRole.ADMIN.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="admin_required")
    return user
