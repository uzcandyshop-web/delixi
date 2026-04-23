"""SQLAlchemy ORM models for DELIXI."""
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import (
    String, Integer, Boolean, Numeric, ForeignKey, BigInteger,
    DateTime, CheckConstraint, Index, text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class UserRole(str, Enum):
    CUSTOMER = "customer"
    SELLER = "seller"
    ADMIN = "admin"


class LedgerReason(str, Enum):
    PURCHASE = "purchase"
    REDEEM = "redeem"
    ADJUST = "adjust"
    EXPIRE = "expire"


class RedemptionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ISSUED = "issued"


# ---------- Regions ----------
class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    name_ru: Mapped[str] = mapped_column(String(128), nullable=False)
    name_uz: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    users: Mapped[list["User"]] = relationship(back_populates="region")


# ---------- Users ----------
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(200))
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default=UserRole.CUSTOMER.value)
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="ru")
    qr_token: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    region: Mapped["Region"] = relationship(back_populates="users")

    __table_args__ = (
        CheckConstraint("role IN ('customer','seller','admin')", name="chk_user_role"),
        CheckConstraint("language IN ('ru','uz')", name="chk_user_language"),
        Index("idx_users_region", "region_id"),
        Index("idx_users_role", "role"),
    )


# ---------- Bonus tiers ----------
class BonusTier(Base):
    __tablename__ = "bonus_tiers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    min_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    max_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )


# ---------- Transactions ----------
class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    bonus_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    bonus_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    customer: Mapped["User"] = relationship(foreign_keys=[customer_id])
    seller: Mapped["User"] = relationship(foreign_keys=[seller_id])
    region: Mapped["Region"] = relationship()

    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_tx_amount_positive"),
        Index("idx_tx_customer", "customer_id", "created_at"),
        Index("idx_tx_seller", "seller_id", "created_at"),
        Index("idx_tx_region", "region_id", "created_at"),
    )


# ---------- Bonus ledger (event-sourcing) ----------
class BonusLedger(Base):
    __tablename__ = "bonus_ledger"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    delta: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str] = mapped_column(String(32), nullable=False)
    tx_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transactions.id")
    )
    redemption_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    __table_args__ = (
        CheckConstraint(
            "reason IN ('purchase','redeem','adjust','expire')", name="chk_ledger_reason"
        ),
        Index("idx_ledger_user", "user_id", "created_at"),
    )


# ---------- Prizes ----------
class Prize(Base):
    __tablename__ = "prizes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    cost_bonus: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    image_url: Mapped[str | None] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )


# ---------- Redemptions ----------
class Redemption(Base):
    __tablename__ = "redemptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    prize_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prizes.id"), nullable=False
    )
    cost_bonus: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=RedemptionStatus.PENDING.value
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    note: Mapped[str | None] = mapped_column(String)

    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    prize: Mapped["Prize"] = relationship()
    resolver: Mapped["User"] = relationship(foreign_keys=[resolved_by])

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','approved','rejected','issued')", name="chk_redemption_status"
        ),
    )
