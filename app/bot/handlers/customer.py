"""Customer-facing bot handlers: registration FSM + main menu."""
import logging
from decimal import Decimal
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove,
    BufferedInputFile,
)
from app.config import get_settings
from app.core.qr import qr_encode
from app.core.qr_image import make_qr_png
from app.db import SessionLocal
from app.models import User, Region, UserRole, Transaction, Prize
from app.services.bonus import get_balance
from app.services.redemptions import request_redemption, RedemptionError

log = logging.getLogger("delixi.bot.customer")
router = Router()
settings = get_settings()


# ---------- FSM ----------
class Registration(StatesGroup):
    awaiting_phone = State()
    awaiting_region = State()


def _main_kb(role: str) -> ReplyKeyboardMarkup:
    """Role-aware main menu keyboard (client-side layout)."""
    if role == UserRole.CUSTOMER.value:
        rows = [
            [KeyboardButton(text="📱 Мой QR"), KeyboardButton(text="💰 Баланс")],
            [KeyboardButton(text="🎁 Призы"), KeyboardButton(text="📜 История")],
            [KeyboardButton(text="❓ Помощь")],
        ]
    else:
        rows = [[KeyboardButton(text="📱 Открыть меню")]]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


# ---------- /start ----------
@router.message(CommandStart())
async def start(m: Message, state: FSMContext):
    await state.clear()
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
        if user:
            await m.answer(
                f"С возвращением, {user.full_name or 'друг'}!",
                reply_markup=_main_kb(user.role),
            )
            return

    # If user is in ADMIN_TG_IDS, we'll still require phone, but assign admin role.
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить номер", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await m.answer(
        "👋 Добро пожаловать в <b>DELIXI</b>!\n\n"
        "Это бонусная программа для постоянных клиентов. "
        "Поделитесь номером телефона, чтобы зарегистрироваться:",
        reply_markup=kb,
    )
    await state.set_state(Registration.awaiting_phone)


@router.message(Registration.awaiting_phone, F.contact)
async def got_contact(m: Message, state: FSMContext):
    contact = m.contact
    if contact.user_id != m.from_user.id:
        await m.answer("Пожалуйста, отправьте <b>свой</b> контакт.")
        return

    await state.update_data(
        phone=contact.phone_number,
        full_name=f"{m.from_user.first_name or ''} {m.from_user.last_name or ''}".strip(),
    )

    with SessionLocal() as db:
        regions = (
            db.query(Region)
            .filter(Region.is_active.is_(True))
            .order_by(Region.name_ru)
            .all()
        )
    if not regions:
        await m.answer("Регионы ещё не настроены. Свяжитесь с администратором.")
        await state.clear()
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=r.name_ru, callback_data=f"reg:{r.id}")]
            for r in regions
        ]
    )
    await m.answer("Выберите ваш регион:", reply_markup=kb)
    await state.set_state(Registration.awaiting_region)


@router.callback_query(Registration.awaiting_region, F.data.startswith("reg:"))
async def got_region(cb: CallbackQuery, state: FSMContext):
    region_id = int(cb.data.split(":", 1)[1])
    data = await state.get_data()

    with SessionLocal() as db:
        region = db.get(Region, region_id)
        if not region:
            await cb.answer("Регион не найден", show_alert=True)
            return

        role = (
            UserRole.ADMIN.value
            if cb.from_user.id in settings.admin_tg_id_set
            else UserRole.CUSTOMER.value
        )

        # Create user with a placeholder token, then fill in the real one
        # once we know the DB-generated UUID.
        user = User(
            telegram_id=cb.from_user.id,
            phone=data["phone"],
            full_name=data.get("full_name") or None,
            region_id=region.id,
            role=role,
            qr_token="pending",
        )
        db.add(user)
        db.flush()
        user.qr_token = qr_encode(str(user.id))
        db.commit()
        db.refresh(user)

        qr_token = user.qr_token
        role_saved = user.role
        name = user.full_name or cb.from_user.first_name

    await cb.message.edit_reply_markup()
    await cb.answer()

    if role_saved == UserRole.CUSTOMER.value:
        png = make_qr_png(qr_token)
        await cb.message.answer_photo(
            BufferedInputFile(png, filename="qr.png"),
            caption=(
                f"Готово, <b>{name}</b>! 🎉\n\n"
                "Показывайте этот QR-код продавцу при покупке — "
                "бонусы начислятся автоматически."
            ),
            reply_markup=_main_kb(role_saved),
        )
    else:
        await cb.message.answer(
            f"Добро пожаловать, <b>{name}</b>! Роль: <b>{role_saved}</b>.",
            reply_markup=_main_kb(role_saved),
        )
    await state.clear()


# ---------- Main menu handlers ----------
def _get_user(telegram_id: int) -> User | None:
    with SessionLocal() as db:
        return db.query(User).filter(User.telegram_id == telegram_id).first()


@router.message(F.text == "📱 Мой QR")
async def show_qr(m: Message):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
        if not user:
            await m.answer("Сначала зарегистрируйтесь через /start")
            return
        token = user.qr_token
    png = make_qr_png(token)
    await m.answer_photo(
        BufferedInputFile(png, filename="qr.png"),
        caption="Ваш персональный QR-код",
    )


def _fmt(n: Decimal) -> str:
    q = n.quantize(Decimal("1")) if n == n.to_integral_value() else n
    return f"{q:,}".replace(",", " ")


@router.message(F.text == "💰 Баланс")
async def show_balance(m: Message):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
        if not user:
            await m.answer("Сначала зарегистрируйтесь через /start")
            return
        balance = get_balance(db, user.id)
    await m.answer(f"💰 <b>Баланс:</b> {_fmt(balance)} бонусов")


@router.message(F.text == "📜 История")
async def show_history(m: Message):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
        if not user:
            await m.answer("Сначала зарегистрируйтесь через /start")
            return
        rows = (
            db.query(Transaction)
            .filter(Transaction.customer_id == user.id)
            .order_by(Transaction.created_at.desc())
            .limit(10)
            .all()
        )
    if not rows:
        await m.answer("История покупок пуста.")
        return
    lines = ["<b>Последние 10 покупок:</b>\n"]
    for r in rows:
        date = r.created_at.strftime("%d.%m.%Y %H:%M")
        lines.append(
            f"• {date} — <b>{_fmt(r.amount)}</b> сум "
            f"(+{_fmt(r.bonus_amount)} бонусов)"
        )
    await m.answer("\n".join(lines))


@router.message(F.text == "🎁 Призы")
async def show_prizes(m: Message):
    with SessionLocal() as db:
        prizes = (
            db.query(Prize)
            .filter(Prize.is_active.is_(True), Prize.stock > 0)
            .order_by(Prize.cost_bonus)
            .limit(20)
            .all()
        )
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
        balance = get_balance(db, user.id) if user else Decimal("0")

    if not prizes:
        await m.answer("Каталог призов пока пуст.")
        return

    await m.answer(f"🎁 <b>Каталог призов</b>\nВаш баланс: <b>{_fmt(balance)}</b>")
    for p in prizes:
        affordable = balance >= p.cost_bonus
        kb = None
        if affordable:
            kb = InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text=f"Заказать за {_fmt(p.cost_bonus)}",
                        callback_data=f"redeem:{p.id}",
                    )
                ]]
            )
        text = (
            f"<b>{p.name}</b>\n"
            f"Стоимость: <b>{_fmt(p.cost_bonus)}</b> бонусов\n"
            f"В наличии: {p.stock} шт."
        )
        if p.description:
            text += f"\n\n{p.description}"
        await m.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("redeem:"))
async def redeem_callback(cb: CallbackQuery):
    prize_id = cb.data.split(":", 1)[1]
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == cb.from_user.id).first()
        if not user or user.role != UserRole.CUSTOMER.value:
            await cb.answer("Только клиенты могут заказывать призы", show_alert=True)
            return
        try:
            red = request_redemption(db, user, prize_id)
        except RedemptionError as e:
            messages = {
                "prize_not_found": "Приз не найден",
                "out_of_stock": "Приз закончился",
                "insufficient_balance": (
                    f"Недостаточно бонусов (нужно {e.extra.get('required')}, "
                    f"у вас {e.extra.get('balance')})"
                ),
            }
            await cb.answer(messages.get(e.code, e.code), show_alert=True)
            return
        prize_name = red.prize.name

    await cb.answer()
    await cb.message.edit_reply_markup()
    await cb.message.answer(
        f"✅ Заявка на <b>{prize_name}</b> оформлена!\n\n"
        "Админ рассмотрит её в ближайшее время. "
        "Бонусы спишутся только после подтверждения."
    )


@router.message(F.text == "❓ Помощь")
async def help_msg(m: Message):
    await m.answer(
        "<b>Как это работает:</b>\n\n"
        "1. Показывайте QR-код продавцу при каждой покупке\n"
        "2. Получайте бонусы автоматически (процент зависит от суммы)\n"
        "3. Копите и меняйте на призы из каталога\n\n"
        "По вопросам: @delixi_support"
    )


@router.message(Command("qr"))
async def qr_cmd(m: Message):
    await show_qr(m)
