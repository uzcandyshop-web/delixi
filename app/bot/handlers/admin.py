"""Admin handlers: pending redemption approval, seller management, localized."""
import logging
from decimal import Decimal
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
)
from app.config import get_settings
from app.core.i18n import t, DEFAULT_LANG
from app.db import SessionLocal
from app.models import User, Redemption, UserRole, Region
from app.services.redemptions import (
    approve_redemption, reject_redemption, RedemptionError,
)
from app.bot.notify import (
    notify_redemption_approved, notify_redemption_rejected,
)

log = logging.getLogger("delixi.bot.admin")
router = Router()
settings = get_settings()


def _is_admin(telegram_id: int) -> bool:
    if telegram_id in settings.admin_tg_id_set:
        return True
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        return bool(user and user.role == UserRole.ADMIN.value)


def _admin_lang(telegram_id: int) -> str:
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        return user.language if user else DEFAULT_LANG


def _fmt(n: Decimal) -> str:
    q = n.quantize(Decimal("1")) if n == n.to_integral_value() else n
    return f"{q:,}".replace(",", " ")


@router.message(Command("admin"))
async def admin_menu(m: Message):
    if not _is_admin(m.from_user.id):
        return
    lang = _admin_lang(m.from_user.id)
    await m.answer(t("admin_menu", lang))


@router.message(Command("pending"))
async def list_pending(m: Message):
    if not _is_admin(m.from_user.id):
        return
    lang = _admin_lang(m.from_user.id)
    with SessionLocal() as db:
        rows = (
            db.query(Redemption)
            .filter(Redemption.status == "pending")
            .order_by(Redemption.requested_at)
            .limit(20)
            .all()
        )
        items = [(r.id, r.prize.name, r.cost_bonus, r.user.full_name or str(r.user.telegram_id))
                 for r in rows]

    if not items:
        await m.answer(t("no_pending", lang))
        return

    for red_id, prize_name, cost, customer_name in items:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=t("approve_btn", lang), callback_data=f"adm:approve:{red_id}"),
            InlineKeyboardButton(text=t("reject_btn", lang), callback_data=f"adm:reject:{red_id}"),
        ]])
        await m.answer(
            t("pending_item", lang, customer=customer_name, prize=prize_name, cost=_fmt(cost)),
            reply_markup=kb,
        )


@router.callback_query(F.data.startswith("adm:"))
async def resolve_redemption(cb: CallbackQuery):
    lang = _admin_lang(cb.from_user.id)
    if not _is_admin(cb.from_user.id):
        await cb.answer(t("no_access", lang), show_alert=True)
        return
    _, action, red_id = cb.data.split(":", 2)

    with SessionLocal() as db:
        admin = db.query(User).filter(User.telegram_id == cb.from_user.id).first()
        if not admin:
            await cb.answer(t("register_first", lang), show_alert=True)
            return
        try:
            if action == "approve":
                red = approve_redemption(db, admin, red_id)
            else:
                red = reject_redemption(db, admin, red_id, note=None)
        except RedemptionError as e:
            await cb.answer(f"Error: {e.code}", show_alert=True)
            return
        customer_tg = red.user.telegram_id
        customer_lang = red.user.language
        prize_name = red.prize.name
        status = red.status

    await cb.message.edit_reply_markup()
    await cb.answer(t("done", lang))
    if status == "approved":
        await cb.message.answer(t("redemption_approved", lang))
        await notify_redemption_approved(customer_tg, prize_name, customer_lang)
    else:
        await cb.message.answer(t("redemption_rejected", lang))
        await notify_redemption_rejected(customer_tg, prize_name, None, customer_lang)


@router.message(Command("sellers"))
async def list_sellers(m: Message):
    if not _is_admin(m.from_user.id):
        return
    lang = _admin_lang(m.from_user.id)
    with SessionLocal() as db:
        rows = (
            db.query(User)
            .filter(User.role == UserRole.SELLER.value)
            .order_by(User.created_at.desc())
            .limit(50)
            .all()
        )
        items = [
            (u.telegram_id, u.full_name or "—", u.region.name_ru,
             "✅" if u.is_active else "⛔")
            for u in rows
        ]
    if not items:
        await m.answer(t("sellers_empty", lang))
        return
    lines = [t("sellers_header", lang)]
    for tg_id, name, region, active in items:
        lines.append(f"{active} <code>{tg_id}</code> — {name} ({region})")
    await m.answer("\n".join(lines))


@router.message(Command("make_seller"))
async def make_seller(m: Message):
    if not _is_admin(m.from_user.id):
        return
    lang = _admin_lang(m.from_user.id)
    parts = (m.text or "").split()
    if len(parts) != 3:
        await m.answer(t("make_seller_usage", lang))
        return
    try:
        tg_id = int(parts[1])
    except ValueError:
        await m.answer(t("make_seller_id_must_be_number", lang))
        return
    region_code = parts[2].upper()

    with SessionLocal() as db:
        region = db.query(Region).filter(Region.code == region_code).first()
        if not region:
            await m.answer(t("region_not_found_code", lang, code=region_code))
            return
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if not user:
            await m.answer(t("user_not_found_ask_start", lang, tg_id=tg_id))
            return
        user.role = UserRole.SELLER.value
        user.region_id = region.id
        user.is_active = True
        db.commit()
        name = user.full_name or str(tg_id)

    await m.answer(t("made_seller", lang, name=name, code=region_code))
