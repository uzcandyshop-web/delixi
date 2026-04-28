"""Seller handlers: inline WebApp scanner + multi-period report."""
from decimal import Decimal
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo,
    InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile,
)

from app.config import get_settings
from app.core.i18n import t, SUPPORTED_LANGS, DEFAULT_LANG
from app.core.chart import make_daily_chart
from app.db import SessionLocal
from app.models import User, UserRole
from app.services.reports import seller_report

router = Router()
settings = get_settings()


def _in_any(key: str):
    texts = {t(key, lang) for lang in SUPPORTED_LANGS}
    return F.text.in_(texts)


def _seller_reply_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("menu_scan", lang))],
            [KeyboardButton(text=t("menu_today", lang))],
            [KeyboardButton(text=t("menu_language", lang))],
        ],
        resize_keyboard=True,
    )


def _scan_inline_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=t("menu_scan", lang),
            web_app=WebAppInfo(url=settings.webapp_url),
        )
    ]])


def _periods_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("rep_today", lang), callback_data="rep:s:today"),
        InlineKeyboardButton(text=t("rep_week", lang), callback_data="rep:s:week"),
        InlineKeyboardButton(text=t("rep_month", lang), callback_data="rep:s:month"),
    ]])


def _fmt(n: Decimal) -> str:
    q = n.quantize(Decimal("1")) if n == n.to_integral_value() else n
    return f"{q:,}".replace(",", " ")


# ---------- /seller, /scan ----------
@router.message(Command("seller"))
async def seller_menu(m: Message):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
    lang = user.language if user else DEFAULT_LANG
    if not user or user.role != UserRole.SELLER.value:
        await m.answer(t("not_seller", lang))
        return
    await m.answer(t("seller_menu_intro", lang), reply_markup=_seller_reply_kb(lang))
    await m.answer(t("menu_scan", lang), reply_markup=_scan_inline_kb(lang))


@router.message(Command("scan"))
async def scan_cmd(m: Message):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
    lang = user.language if user else DEFAULT_LANG
    if not user or user.role != UserRole.SELLER.value:
        await m.answer(t("not_seller", lang))
        return
    await m.answer(t("menu_scan", lang), reply_markup=_scan_inline_kb(lang))


@router.message(_in_any("menu_scan"))
async def scan_button(m: Message):
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


# ---------- "Сегодня" → period picker ----------
@router.message(_in_any("menu_today"))
async def report_picker(m: Message):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
        if not user or user.role != UserRole.SELLER.value:
            await m.answer(t("only_sellers", DEFAULT_LANG))
            return
        lang = user.language
    await m.answer(t("rep_choose_period", lang), reply_markup=_periods_kb(lang))


@router.callback_query(F.data.startswith("rep:s:"))
async def seller_report_cb(cb: CallbackQuery):
    period = cb.data.split(":", 2)[2]
    if period not in ("today", "week", "month"):
        await cb.answer()
        return

    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == cb.from_user.id).first()
        if not user or user.role != UserRole.SELLER.value:
            await cb.answer(t("only_sellers", DEFAULT_LANG), show_alert=True)
            return
        lang = user.language
        report = seller_report(db, user, period)

    await cb.answer()
    await cb.message.edit_reply_markup()  # remove buttons from prompt

    # Always send text summary
    if report.count == 0:
        await cb.message.answer(t(f"rep_seller_empty_{period}", lang))
        return

    summary = t(
        "rep_seller_summary", lang,
        period=t(f"rep_period_label_{period}", lang),
        count=report.count,
        total=_fmt(report.total),
        bonus=_fmt(report.bonus),
        avg=_fmt(report.avg_check),
    )
    await cb.message.answer(summary)

    # For week/month: PNG chart with daily revenue
    if period in ("week", "month"):
        title = t(f"rep_chart_title_{period}", lang)
        sub = t(
            "rep_chart_subtitle", lang,
            count=report.count, total=_fmt(report.total),
        )
        png = make_daily_chart(
            title=title, subtitle=sub,
            daily=[(d, rev) for d, rev, _ in report.daily],
            lang=lang,
        )
        await cb.message.answer_photo(
            BufferedInputFile(png, filename="chart.png"),
        )
