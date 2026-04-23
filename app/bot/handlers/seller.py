"""Seller handlers: WebApp scanner launch + today's report, localized."""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo,
)
from sqlalchemy import func
from app.config import get_settings
from app.core.i18n import t, SUPPORTED_LANGS, DEFAULT_LANG
from app.db import SessionLocal
from app.models import User, Transaction, UserRole

router = Router()
settings = get_settings()


def _in_any(key: str):
    texts = {t(key, lang) for lang in SUPPORTED_LANGS}
    return F.text.in_(texts)


def _seller_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text=t("menu_scan", lang),
                web_app=WebAppInfo(url=settings.webapp_url),
            )],
            [KeyboardButton(text=t("menu_today", lang))],
            [KeyboardButton(text=t("menu_language", lang))],
        ],
        resize_keyboard=True,
    )


def _fmt(n: Decimal) -> str:
    q = n.quantize(Decimal("1")) if n == n.to_integral_value() else n
    return f"{q:,}".replace(",", " ")


@router.message(Command("seller"))
async def seller_menu(m: Message):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
    lang = user.language if user else DEFAULT_LANG
    if not user or user.role != UserRole.SELLER.value:
        await m.answer(t("not_seller", lang))
        return
    await m.answer(t("seller_menu_intro", lang), reply_markup=_seller_kb(lang))


@router.message(_in_any("menu_open"))
async def seller_open(m: Message):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
    if user and user.role == UserRole.SELLER.value:
        await m.answer(t("seller_menu_reopen", user.language), reply_markup=_seller_kb(user.language))


@router.message(_in_any("menu_today"))
async def today_report(m: Message):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
        if not user or user.role != UserRole.SELLER.value:
            await m.answer(t("only_sellers", DEFAULT_LANG))
            return
        lang = user.language

        since = datetime.now(timezone.utc) - timedelta(hours=24)
        agg = (
            db.query(
                func.count(Transaction.id),
                func.coalesce(func.sum(Transaction.amount), 0),
                func.coalesce(func.sum(Transaction.bonus_amount), 0),
            )
            .filter(
                Transaction.seller_id == user.id,
                Transaction.created_at >= since,
            )
            .one()
        )
        count, total, bonus = agg

    if count == 0:
        await m.answer(t("today_empty", lang))
        return
    await m.answer(t(
        "today_report", lang,
        count=count,
        total=_fmt(Decimal(total)),
        bonus=_fmt(Decimal(bonus)),
    ))
