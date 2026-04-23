"""Pydantic schemas for API request/response."""
from decimal import Decimal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


# ---------- Transactions ----------
class TxCreate(BaseModel):
    qr_token: str = Field(..., min_length=10, max_length=256)
    amount: Decimal = Field(..., gt=0)
    idempotency_key: str = Field(..., min_length=8, max_length=64)


class TxCustomerInfo(BaseModel):
    name: str | None
    region: str


class TxResult(BaseModel):
    transaction_id: UUID
    customer: TxCustomerInfo
    amount: Decimal
    bonus_percent: Decimal
    bonus_amount: Decimal
    balance_after: Decimal
    replayed: bool = False


# ---------- Me ----------
class MeResponse(BaseModel):
    id: UUID
    telegram_id: int
    full_name: str | None
    phone: str
    role: str
    region: str
    balance: Decimal


class HistoryItem(BaseModel):
    id: UUID
    amount: Decimal
    bonus_amount: Decimal
    created_at: datetime


# ---------- Regions ----------
class RegionOut(BaseModel):
    id: int
    code: str
    name_ru: str
    name_uz: str


# ---------- Prizes ----------
class PrizeOut(BaseModel):
    id: UUID
    name: str
    description: str | None
    cost_bonus: Decimal
    stock: int
    image_url: str | None


class RedemptionCreate(BaseModel):
    prize_id: UUID


class RedemptionOut(BaseModel):
    id: UUID
    prize_id: UUID
    prize_name: str
    cost_bonus: Decimal
    status: str
    requested_at: datetime
    resolved_at: datetime | None
    note: str | None


# ---------- Admin ----------
class TierUpsert(BaseModel):
    min_amount: Decimal = Field(..., ge=0)
    max_amount: Decimal | None = None
    percent: Decimal = Field(..., ge=0, le=100)


class TiersUpdate(BaseModel):
    tiers: list[TierUpsert]


class ResolveRedemption(BaseModel):
    action: str  # "approve" | "reject"
    note: str | None = None
