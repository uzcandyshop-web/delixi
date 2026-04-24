"""Customer-facing bot handlers: language selection, registration FSM, main menu."""
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
from app.core.prize_card import make_prize_card
from app.core.i18n import t, LANG_NAMES, SUPPORTED_LANGS, DEFAULT_LANG, normalize_lang
from app.db import SessionLocal
from app.models import User, Region, UserRole, Transaction, Prize
from app.services.bonus import get_balance
from app.services.redemptions import request_redemption, RedemptionError

log = logging.getLogger("delixi.bot.customer")
router = Router()
settings = get_settings()


# ---------- FSM ----------
class Registration(StatesGroup):
    awaiting_language = State()
    awaiting_phone = State()
    awaiting_full_name = State()
    awaiting_region = State()


class LangChange(StatesGroup):
    awaiting_language = State()


# ---------- Helpers ----------
def _lang_kb() -> InlineKeyboardMarkup:
    """Inline keyboard to pick a language."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=LANG_NAMES[code], callback_data=f"lang:{code}")]
            for code in SUPPORTED_LANGS
        ]
    )


def _main_kb(role: str, lang: str) -> ReplyKeyboardMarkup:
    """Role-aware main menu keyboard in the user's language."""
    if role == UserRole.CUSTOMER.value:
        rows = [
            [KeyboardButton(text=t("menu_qr", lang)), KeyboardButton(text=t("menu_balance", lang))],
            [KeyboardButton(text=t("menu_prizes", lang)), KeyboardButton(text=t("menu_history", lang))],
            [KeyboardButton(text=t("menu_help", lang)), KeyboardButton(text=t("menu_language", lang))],
        ]
    else:
        rows = [
            [KeyboardButton(text=t("menu_open", lang))],
            [KeyboardButton(text=t("menu_language", lang))],
        ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def _get_user_lang(telegram_id: int) -> str:
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        return user.language if user else DEFAULT_LANG


def _in_any(key: str):
    """Build a filter matching a localized button text in any supported language."""
    texts = {t(key, lang) for lang in SUPPORTED_LANGS}
    return F.text.in_(texts)


# ---------- /start ----------
@router.message(CommandStart())
async def start(m: Message, state: FSMContext):
    await state.clear()
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
        if user:
            lang = user.language
            await m.answer(
                t("welcome_back", lang, name=user.full_name or "друг"),
                reply_markup=_main_kb(user.role, lang),
            )
            return

    await m.answer(t("choose_language", DEFAULT_LANG), reply_markup=_lang_kb())
    await state.set_state(Registration.awaiting_language)


@router.callback_query(Registration.awaiting_language, F.data.startswith("lang:"))
async def picked_language(cb: CallbackQuery, state: FSMContext):
    lang = normalize_lang(cb.data.split(":", 1)[1])
    await state.update_data(language=lang)

    await cb.message.edit_reply_markup()
    await cb.answer()

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("send_phone_btn", lang), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await cb.message.answer(t("start_welcome", lang), reply_markup=kb)
    await state.set_state(Registration.awaiting_phone)


# ---------- Phone ----------
@router.message(Registration.awaiting_phone, F.contact)
async def got_contact(m: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", DEFAULT_LANG)

    contact = m.contact
    if contact.user_id != m.from_user.id:
        await m.answer(t("send_own_contact", lang))
        return

    await state.update_data(phone=contact.phone_number)
    await m.answer(t("ask_full_name", lang), reply_markup=ReplyKeyboardRemove())
    await state.set_state(Registration.awaiting_full_name)


# ---------- Full name ----------
@router.message(Registration.awaiting_full_name, F.text)
async def got_full_name(m: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("language", DEFAULT_LANG)
    full_name = (m.text or "").strip()

    if len(full_name) < 5:
        await m.answer(t("err_name_too_short", lang))
        return
    if len(full_name) > 120:
        await m.answer(t("err_name_too_long", lang))
        return
    if len(full_name.split()) < 2:
        await m.answer(t("err_name_need_two_words", lang))
        return
    if not any(ch.isalpha() for ch in full_name):
        await m.answer(t("err_name_no_letters", lang))
        return

    await state.update_data(full_name=full_name)

    with SessionLocal() as db:
        regions = (
            db.query(Region)
            .filter(Region.is_active.is_(True))
            .order_by(Region.name_ru)
            .all()
        )
    if not regions:
        await m.answer(t("no_regions", lang))
        await state.clear()
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=(r.name_uz if lang == "uz" else r.name_ru),
                callback_data=f"reg:{r.id}",
            )]
            for r in regions
        ]
    )
    await m.answer(t("thanks_choose_region", lang, name=full_name), reply_markup=kb)
    await state.set_state(Registration.awaiting_region)


# ---------- Region ----------
@router.callback_query(Registration.awaiting_region, F.data.startswith("reg:"))
async def got_region(cb: CallbackQuery, state: FSMContext):
    region_id = int(cb.data.split(":", 1)[1])
    data = await state.get_data()
    lang = data.get("language", DEFAULT_LANG)

    if not data.get("phone") or not data.get("full_name"):
        await cb.answer(t("session_expired", lang), show_alert=True)
        await state.clear()
        return

    with SessionLocal() as db:
        region = db.get(Region, region_id)
        if not region:
            await cb.answer(t("region_not_found", lang), show_alert=True)
            return

        role = (
            UserRole.ADMIN.value
            if cb.from_user.id in settings.admin_tg_id_set
            else UserRole.CUSTOMER.value
        )

        user = User(
            telegram_id=cb.from_user.id,
            phone=data["phone"],
            full_name=data["full_name"],
            region_id=region.id,
            role=role,
            language=lang,
            qr_token="pending",
        )
        db.add(user)
        db.flush()
        user.qr_token = qr_encode(str(user.id))
        db.commit()
        db.refresh(user)

        qr_token = user.qr_token
        role_saved = user.role
        name = user.full_name

    await cb.message.edit_reply_markup()
    await cb.answer()

    if role_saved == UserRole.CUSTOMER.value:
        png = make_qr_png(qr_token)
        await cb.message.answer_photo(
            BufferedInputFile(png, filename="qr.png"),
            caption=t("qr_ready_customer", lang, name=name),
            reply_markup=_main_kb(role_saved, lang),
        )
    else:
        await cb.message.answer(
            t("welcome_staff", lang, name=name, role=role_saved),
            reply_markup=_main_kb(role_saved, lang),
        )
    await state.clear()


# ---------- /language ----------
@router.message(Command("language"))
async def cmd_language(m: Message, state: FSMContext):
    await state.clear()
    await m.answer(t("choose_language", DEFAULT_LANG), reply_markup=_lang_kb())
    await state.set_state(LangChange.awaiting_language)


@router.message(_in_any("menu_language"))
async def menu_language(m: Message, state: FSMContext):
    await cmd_language(m, state)


@router.callback_query(LangChange.awaiting_language, F.data.startswith("lang:"))
async def lang_change_picked(cb: CallbackQuery, state: FSMContext):
    lang = normalize_lang(cb.data.split(":", 1)[1])

    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == cb.from_user.id).first()
        if user:
            user.language = lang
            db.commit()
            role = user.role
        else:
            role = None

    await cb.message.edit_reply_markup()
    await cb.answer()
    if role:
        await cb.message.answer(t("language_set", lang), reply_markup=_main_kb(role, lang))
    else:
        await cb.message.answer(t("language_set", lang))
        await cb.message.answer(t("not_registered", lang))
    await state.clear()


# ---------- Main menu handlers ----------
@router.message(_in_any("menu_qr"))
async def show_qr(m: Message):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
        if not user:
            await m.answer(t("not_registered", DEFAULT_LANG))
            return
        token = user.qr_token
        lang = user.language
    png = make_qr_png(token)
    await m.answer_photo(
        BufferedInputFile(png, filename="qr.png"),
        caption=t("qr_caption", lang),
    )


def _fmt(n: Decimal) -> str:
    q = n.quantize(Decimal("1")) if n == n.to_integral_value() else n
    return f"{q:,}".replace(",", " ")


@router.message(_in_any("menu_balance"))
async def show_balance(m: Message):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
        if not user:
            await m.answer(t("not_registered", DEFAULT_LANG))
            return
        balance = get_balance(db, user.id)
        lang = user.language
    await m.answer(t("balance_label", lang, amount=_fmt(balance)))


@router.message(_in_any("menu_history"))
async def show_history(m: Message):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
        if not user:
            await m.answer(t("not_registered", DEFAULT_LANG))
            return
        lang = user.language
        rows = (
            db.query(Transaction)
            .filter(Transaction.customer_id == user.id)
            .order_by(Transaction.created_at.desc())
            .limit(10)
            .all()
        )
    if not rows:
        await m.answer(t("history_empty", lang))
        return
    lines = [t("history_header", lang)]
    sum_suffix = t("history_item_suffix_sum", lang)
    bonus_suffix = t("history_item_suffix_bonus", lang)
    for r in rows:
        date = r.created_at.strftime("%d.%m.%Y %H:%M")
        lines.append(
            f"• {date} — <b>{_fmt(r.amount)}</b> {sum_suffix} "
            f"(+{_fmt(r.bonus_amount)} {bonus_suffix})"
        )
    await m.answer("\n".join(lines))


@router.message(_in_any("menu_prizes"))
async def show_prizes(m: Message):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
        if not user:
            await m.answer(t("not_registered", DEFAULT_LANG))
            return
        lang = user.language
        balance = get_balance(db, user.id)
        prizes = (
            db.query(Prize)
            .filter(Prize.is_active.is_(True), Prize.stock > 0)
            .order_by(Prize.cost_bonus)
            .limit(10)
            .all()
        )

    if not prizes:
        await m.answer(t("prizes_empty", lang))
        return

    await m.answer(t("prizes_header", lang, balance=_fmt(balance)))
    for p in prizes:
        affordable = balance >= p.cost_bonus
        kb = None
        if affordable:
            kb = InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text=t("prize_order_btn", lang, cost=_fmt(p.cost_bonus)),
                        callback_data=f"redeem:{p.id}",
                    )
                ]]
            )

        # Caption: stock info + description
        caption_lines = [f"<b>{p.name}</b>"]
        caption_lines.append(t("prize_stock", lang, stock=p.stock))
        if p.description:
            caption_lines.append("")
            caption_lines.append(p.description)
        caption = "\n".join(caption_lines)

        png = make_prize_card(
            prize_name=p.name,
            cost=p.cost_bonus,
            balance=balance,
            lang=lang,
        )
        await m.answer_photo(
            BufferedInputFile(png, filename="prize.png"),
            caption=caption,
            reply_markup=kb,
        )


@router.callback_query(F.data.startswith("redeem:"))
async def redeem_callback(cb: CallbackQuery):
    prize_id = cb.data.split(":", 1)[1]
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == cb.from_user.id).first()
        if not user or user.role != UserRole.CUSTOMER.value:
            await cb.answer(t("only_customers_redeem", DEFAULT_LANG), show_alert=True)
            return
        lang = user.language
        try:
            red = request_redemption(db, user, prize_id)
        except RedemptionError as e:
            if e.code == "prize_not_found":
                msg = t("prize_not_found", lang)
            elif e.code == "out_of_stock":
                msg = t("prize_out_of_stock", lang)
            elif e.code == "insufficient_balance":
                msg = t(
                    "insufficient_balance", lang,
                    required=e.extra.get("required"),
                    balance=e.extra.get("balance"),
                )
            else:
                msg = e.code
            await cb.answer(msg, show_alert=True)
            return
        prize_name = red.prize.name

    await cb.answer()
    await cb.message.edit_reply_markup()
    await cb.message.answer(t("redemption_submitted", lang, prize=prize_name))


@router.message(_in_any("menu_help"))
async def help_msg(m: Message):
    lang = _get_user_lang(m.from_user.id)
    await m.answer(t("help_text", lang))


@router.message(Command("qr"))
async def qr_cmd(m: Message):
    await show_qr(m)
