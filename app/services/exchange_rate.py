"""USD exchange rate fetching & caching.

Data source: Central Bank of Uzbekistan open JSON API.
URL:   https://cbu.uz/ru/arkhiv-kursov-valyut/json/USD/
Docs:  https://cbu.uz/ru/arkhiv-kursov-valyut/veb-masteram/

The API returns an array of rate entries for the requested currency
for the last week. We always take the most recent entry.

Strategy:
- On every request, points-calculator calls `get_current_rate(db)`:
  returns the last stored rate, or the migration-seeded default.
- A daily background task or admin command calls `update_daily_rate(db)`:
  scrapes cbu.uz and persists a new row if the rate changed.
- All transactions persist the rate they used in their own row
  (Transaction.usd_rate), so historic calculations stay auditable
  even if the rate moves later.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.models import ExchangeRate

log = logging.getLogger("delixi.exchange_rate")

CBU_URL = "https://cbu.uz/ru/arkhiv-kursov-valyut/json/USD/"
FALLBACK_RATE = Decimal("12190.43")
REQUEST_TIMEOUT = 10.0


def get_current_rate(db: Session, currency: str = "USD") -> Decimal:
    """Return the most recent rate for `currency` from the DB.

    Falls back to FALLBACK_RATE if no rows exist (first-time start before
    the migration seed, e.g. in tests).
    """
    row = (
        db.query(ExchangeRate)
        .filter(ExchangeRate.currency == currency)
        .order_by(ExchangeRate.effective_date.desc(), ExchangeRate.id.desc())
        .first()
    )
    if row is None:
        log.warning("No exchange_rates row for %s; using fallback %s", currency, FALLBACK_RATE)
        return FALLBACK_RATE
    return Decimal(row.rate)


def fetch_cbu_rate(currency: str = "USD") -> Optional[tuple[Decimal, date]]:
    """Fetch the latest rate for `currency` from cbu.uz.

    Returns (rate, effective_date) or None on any failure.
    Never raises — caller decides whether to fall back to the cached rate.
    """
    try:
        resp = httpx.get(CBU_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        log.warning("fetch_cbu_rate: HTTP failed: %s", e)
        return None

    if not isinstance(data, list) or not data:
        log.warning("fetch_cbu_rate: unexpected response shape: %r", data[:1] if isinstance(data, list) else data)
        return None

    # API returns newest-first; take the first entry matching currency
    row = next((r for r in data if r.get("Ccy") == currency), None)
    if row is None:
        log.warning("fetch_cbu_rate: no %s row in response", currency)
        return None

    try:
        rate = Decimal(str(row["Rate"]))
        # "Date" is DD.MM.YYYY
        eff_date = datetime.strptime(row["Date"], "%d.%m.%Y").date()
    except Exception as e:
        log.warning("fetch_cbu_rate: parse failed: %s, row=%r", e, row)
        return None

    log.info("fetch_cbu_rate: got %s %s on %s", currency, rate, eff_date)
    return rate, eff_date


def update_daily_rate(db: Session, currency: str = "USD") -> Optional[Decimal]:
    """Fetch fresh rate from cbu.uz and persist it.

    Idempotent — inserting the same (currency, effective_date) twice is a
    no-op because of the unique index. Returns the newly stored rate, or
    None if the fetch failed.
    """
    result = fetch_cbu_rate(currency)
    if result is None:
        return None
    rate, eff_date = result

    existing = (
        db.query(ExchangeRate)
        .filter(
            ExchangeRate.currency == currency,
            ExchangeRate.effective_date == eff_date,
        )
        .first()
    )
    if existing:
        # Already have today's rate; update if the value changed (rare)
        if Decimal(existing.rate) != rate:
            existing.rate = rate
            existing.source = "cbu.uz"
            existing.fetched_at = datetime.utcnow()
            db.commit()
            log.info("Updated existing rate for %s %s -> %s", currency, eff_date, rate)
        return rate

    row = ExchangeRate(
        currency=currency,
        rate=rate,
        source="cbu.uz",
        effective_date=eff_date,
    )
    db.add(row)
    db.commit()
    log.info("Stored new rate: %s %s on %s", currency, rate, eff_date)
    return rate


def ensure_rate_fresh(db: Session, currency: str = "USD") -> Decimal:
    """Ensure we have today's rate; if not, fetch it. Return current rate.

    Called on bot/API startup so the first transaction of the day always
    uses an up-to-date number. If cbu.uz is unreachable, silently returns
    the last known rate — never fails.
    """
    today = date.today()
    latest = (
        db.query(ExchangeRate)
        .filter(ExchangeRate.currency == currency)
        .order_by(ExchangeRate.effective_date.desc())
        .first()
    )
    if latest is None or latest.effective_date < today:
        fetched = update_daily_rate(db, currency)
        if fetched is not None:
            return fetched
    return get_current_rate(db, currency)
