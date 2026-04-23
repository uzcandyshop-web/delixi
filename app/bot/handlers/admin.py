"""Admin handlers: pending redemption approval, seller management."""
import logging
from decimal import Decimal
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
)
from app.config import get_settings
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


def _fmt(n: Decimal) -> str:
    q = n.quantize(Decimal("1")) if n == n.to_integral_value() else n
    return f"{q:,}".replace(",", " ")


@router.message(Command("admin"))
async def admin_menu(m: Message):
    if not _is_admin(m.from_user.id):
        return
    await m.answer(
        "🛠 <b>Админ-панель</b>\n\n"
        "/pending — заявки на призы\n"
        "/sellers — список продавцов\n"
        "/make_seller &lt;telegram_id&gt; &lt;region_code&gt; — назначить продавца\n"
        "/report — оборот за 7 дней"
    )


@router.message(Command("pending"))
async def list_pending(m: Message):
    if not _is_admin(m.from_user.id):
        return
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
        await m.answer("Нет заявок на рассмотрении.")
        return

    for red_id, prize_name, cost, customer_name in items:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"adm:approve:{red_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm:reject:{red_id}"),
        ]])
        await m.answer(
            f"📨 <b>Заявка</b>\n"
            f"Клиент: {customer_name}\n"
            f"Приз: <b>{prize_name}</b>\n"
            f"Стоимость: <b>{_fmt(cost)}</b> бонусов",
            reply_markup=kb,
        )


@router.callback_query(F.data.startswith("adm:"))
async def resolve_redemption(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer("Нет доступа", show_alert=True)
        return
    _, action, red_id = cb.data.split(":", 2)

    with SessionLocal() as db:
        admin = db.query(User).filter(User.telegram_id == cb.from_user.id).first()
        if not admin:
            await cb.answer("Сначала зарегистрируйтесь через /start", show_alert=True)
            return
        try:
            if action == "approve":
                red = approve_redemption(db, admin, red_id)
            else:
                red = reject_redemption(db, admin, red_id, note=None)
        except RedemptionError as e:
            await cb.answer(f"Ошибка: {e.code}", show_alert=True)
            return
        customer_tg = red.user.telegram_id
        prize_name = red.prize.name
        status = red.status

    await cb.message.edit_reply_markup()
    await cb.answer("Готово")
    verb = "одобрена" if status == "approved" else "отклонена"
    await cb.message.answer(f"Заявка {verb}.")

    if status == "approved":
        await notify_redemption_approved(customer_tg, prize_name)
    else:
        await notify_redemption_rejected(customer_tg, prize_name, None)


@router.message(Command("sellers"))
async def list_sellers(m: Message):
    if not _is_admin(m.from_user.id):
        return
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
        await m.answer("Продавцов пока нет. Используйте /make_seller")
        return
    lines = ["<b>Продавцы:</b>\n"]
    for tg_id, name, region, active in items:
        lines.append(f"{active} <code>{tg_id}</code> — {name} ({region})")
    await m.answer("\n".join(lines))


@router.message(Command("make_seller"))
async def make_seller(m: Message):
    if not _is_admin(m.from_user.id):
        return
    parts = (m.text or "").split()
    if len(parts) != 3:
        await m.answer(
            "Использование: <code>/make_seller &lt;telegram_id&gt; &lt;region_code&gt;</code>\n"
            "Пример: <code>/make_seller 123456789 TAS</code>"
        )
        return
    try:
        tg_id = int(parts[1])
    except ValueError:
        await m.answer("telegram_id должен быть числом")
        return
    region_code = parts[2].upper()

    with SessionLocal() as db:
        region = db.query(Region).filter(Region.code == region_code).first()
        if not region:
            await m.answer(f"Регион <b>{region_code}</b> не найден")
            return
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if not user:
            await m.answer(
                f"Пользователь {tg_id} не найден. "
                "Попросите его сначала зарегистрироваться через /start."
            )
            return
        user.role = UserRole.SELLER.value
        user.region_id = region.id
        user.is_active = True
        db.commit()
        name = user.full_name or str(tg_id)

    await m.answer(f"✅ {name} теперь продавец в регионе {region_code}")
