"""Reports: aggregations for seller and admin panels.

Periods:
- 'today'  → last 24h, single number, no chart
- 'week'   → last 7 days incl. today, daily breakdown
- 'month'  → last 30 days incl. today, daily breakdown
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from typing import Literal
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Transaction, User, Region

Period = Literal["today", "week", "month"]


@dataclass
class ReportSummary:
    period: Period
    count: int
    total: Decimal       # revenue in UZS
    bonus: Decimal       # points awarded
    daily: list[tuple[date, Decimal, int]]  # (date, revenue, count) per day
    avg_check: Decimal


def _period_start(period: Period) -> datetime:
    now = datetime.now(timezone.utc)
    if period == "today":
        # Start of today in UTC; could refine to local TZ later.
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "week":
        return (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "month":
        return (now - timedelta(days=29)).replace(hour=0, minute=0, second=0, microsecond=0)
    raise ValueError(f"unknown period: {period}")


def _days_in_period(period: Period) -> int:
    return {"today": 1, "week": 7, "month": 30}[period]


def _build_daily_buckets(
    period: Period, rows: list[tuple[date, Decimal, int]],
) -> list[tuple[date, Decimal, int]]:
    """Pad missing days with zeros so the chart has a complete bar grid."""
    by_date = {d: (rev, cnt) for d, rev, cnt in rows}
    today = datetime.now(timezone.utc).date()
    days = _days_in_period(period)
    result = []
    for offset in range(days - 1, -1, -1):
        d = today - timedelta(days=offset)
        rev, cnt = by_date.get(d, (Decimal("0"), 0))
        result.append((d, rev, cnt))
    return result


def seller_report(db: Session, seller: User, period: Period) -> ReportSummary:
    """Aggregate own transactions for a seller."""
    since = _period_start(period)
    base = db.query(Transaction).filter(
        Transaction.seller_id == seller.id,
        Transaction.created_at >= since,
    )
    agg = base.with_entities(
        func.count(Transaction.id),
        func.coalesce(func.sum(Transaction.amount), 0),
        func.coalesce(func.sum(Transaction.bonus_amount), 0),
    ).one()
    count, total, bonus = agg
    count = int(count or 0)
    total = Decimal(total or 0)
    bonus = Decimal(bonus or 0)

    # Daily breakdown
    daily_rows = base.with_entities(
        func.date(Transaction.created_at).label("d"),
        func.coalesce(func.sum(Transaction.amount), 0),
        func.count(Transaction.id),
    ).group_by(func.date(Transaction.created_at)).all()
    daily_typed = [(r[0], Decimal(r[1] or 0), int(r[2] or 0)) for r in daily_rows]
    daily = _build_daily_buckets(period, daily_typed)

    avg_check = (total / count) if count > 0 else Decimal("0")

    return ReportSummary(
        period=period, count=count, total=total, bonus=bonus,
        daily=daily, avg_check=avg_check,
    )


def admin_report(db: Session, period: Period) -> ReportSummary:
    """System-wide aggregation."""
    since = _period_start(period)
    base = db.query(Transaction).filter(Transaction.created_at >= since)
    agg = base.with_entities(
        func.count(Transaction.id),
        func.coalesce(func.sum(Transaction.amount), 0),
        func.coalesce(func.sum(Transaction.bonus_amount), 0),
    ).one()
    count, total, bonus = agg
    count = int(count or 0)
    total = Decimal(total or 0)
    bonus = Decimal(bonus or 0)

    daily_rows = base.with_entities(
        func.date(Transaction.created_at).label("d"),
        func.coalesce(func.sum(Transaction.amount), 0),
        func.count(Transaction.id),
    ).group_by(func.date(Transaction.created_at)).all()
    daily_typed = [(r[0], Decimal(r[1] or 0), int(r[2] or 0)) for r in daily_rows]
    daily = _build_daily_buckets(period, daily_typed)

    avg_check = (total / count) if count > 0 else Decimal("0")

    return ReportSummary(
        period=period, count=count, total=total, bonus=bonus,
        daily=daily, avg_check=avg_check,
    )


def admin_by_region(db: Session, period: Period) -> list[tuple[str, int, Decimal]]:
    """Per-region (name, count, revenue) for the period, sorted desc by revenue."""
    since = _period_start(period)
    rows = (
        db.query(
            Region.name_ru,
            func.count(Transaction.id),
            func.coalesce(func.sum(Transaction.amount), 0),
        )
        .join(Transaction, Transaction.region_id == Region.id)
        .filter(Transaction.created_at >= since)
        .group_by(Region.name_ru)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )
    return [(name, int(c or 0), Decimal(rev or 0)) for name, c, rev in rows]
