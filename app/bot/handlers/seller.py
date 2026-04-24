"""Seller handlers: inline WebApp scanner launch + today's report, localized.

Uses inline-keyboard WebApp button instead of reply-keyboard, which is the
only way to guarantee signed initData on Telegram Desktop (v9.6+ bug).
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo,
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


def _seller_reply_kb(lang: str) -> ReplyKeyboardMarkup:
    """Bottom reply-keyboard with plain text buttons (no WebApp here)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("menu_scan", lang))],
            [KeyboardButton(text=t("menu_today", lang))],
            [KeyboardButton(text=t("menu_language", lang))],
        ],
        resize_keyboard=True,
    )


def _scan_inline_kb(lang: str) -> InlineKeyboardMarkup:
    """Inline WebApp button — signed initData works on all platforms."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text=t("menu_scan", lang),
                web_app=WebAppInfo(url=settings.webapp_url),
            )
        ]]
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
    # Show bottom menu (for Today/Language buttons)…
    await m.answer(t("seller_menu_intro", lang), reply_markup=_seller_reply_kb(lang))
    # …and an inline scan button in a separate message
    await m.answer(t("menu_scan", lang), reply_markup=_scan_inline_kb(lang))


@router.message(Command("scan"))
async def scan_cmd(m: Message):
    """Quick access to scanner — shows inline WebApp button."""
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
    lang = user.language if user else DEFAULT_LANG
    if not user or user.role != UserRole.SELLER.value:
        await m.answer(t("not_seller", lang))
        return
    await m.answer(t("menu_scan", lang), reply_markup=_scan_inline_kb(lang))


@router.message(_in_any("menu_scan"))
async def scan_button(m: Message):
    """Handle the 📸 button from the reply keyboard — re-send as inline."""
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
    lang = user.language if user else DEFAULT_LANG
    if not user or user.role != UserRole.SELLER.value:
        await m.answer(t("not_seller", lang))
        return
    await m.answer(t("menu_scan", lang), reply_markup=_scan_inline_kb(lang))


@router.message(_in_any("menu_open"))
async def seller_open(m: Message):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
    if user and user.role == UserRole.SELLER.value:
        await m.answer(
            t("seller_menu_reopen", user.language),
            reply_markup=_seller_reply_kb(user.language),
        )
        await m.answer(
            t("menu_scan", user.language),
            reply_markup=_scan_inline_kb(user.language),
        )


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
