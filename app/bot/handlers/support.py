"""Support handlers: client FSM (category → text → photo → submit)
and group-side callbacks for operators (accept / in-progress / resolve / reject).
"""
import logging
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.enums import ChatType

from app.config import get_settings
from app.core.i18n import t, SUPPORTED_LANGS, DEFAULT_LANG
from app.db import SessionLocal
from app.models import User, SupportCategory, SupportStatus
from app.services.support import (
    create_support_request, attach_group_message,
    find_by_group_message, transition_status, SupportError,
)
from app.bot.notify import notify_support_closed

log = logging.getLogger("delixi.bot.support")
router = Router()
settings = get_settings()


# ---------- FSM ----------
class SupportFSM(StatesGroup):
    awaiting_category = State()
    awaiting_text = State()
    awaiting_photo = State()


# ---------- Category metadata ----------
CATEGORY_EMOJI = {
    "engineer": "🔧",
    "complaint": "⚠️",
    "techsupport": "💬",
}


def _in_any(key: str):
    texts = {t(key, lang) for lang in SUPPORTED_LANGS}
    return F.text.in_(texts)


def _short_id(full_id) -> str:
    """First 6 hex chars of UUID, uppercase."""
    return str(full_id).replace("-", "")[:6].upper()


def _cat_label(category: str, lang: str) -> str:
    return t(f"support_cat_{category}", lang)


# ---------- Entry point: ❓ Помощь button or /help ----------
@router.message(_in_any("menu_help"))
async def support_entry(m: Message, state: FSMContext):
    """Replace the old static help text with category picker."""
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
        lang = user.language if user else DEFAULT_LANG
        if not user:
            await m.answer(t("not_registered", DEFAULT_LANG))
            return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("support_cat_engineer", lang), callback_data="sup_cat:engineer")],
        [InlineKeyboardButton(text=t("support_cat_complaint", lang), callback_data="sup_cat:complaint")],
        [InlineKeyboardButton(text=t("support_cat_techsupport", lang), callback_data="sup_cat:techsupport")],
    ])
    await state.clear()
    await m.answer(t("support_choose_category", lang), reply_markup=kb)
    await state.set_state(SupportFSM.awaiting_category)


@router.callback_query(SupportFSM.awaiting_category, F.data.startswith("sup_cat:"))
async def support_picked_category(cb: CallbackQuery, state: FSMContext):
    category = cb.data.split(":", 1)[1]
    if category not in ("engineer", "complaint", "techsupport"):
        await cb.answer()
        return
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == cb.from_user.id).first()
        lang = user.language if user else DEFAULT_LANG

    await state.update_data(category=category, lang=lang)
    await cb.message.edit_reply_markup()
    await cb.answer()
    await cb.message.answer(t("support_ask_text", lang))
    await state.set_state(SupportFSM.awaiting_text)


@router.message(SupportFSM.awaiting_text, F.text)
async def support_got_text(m: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", DEFAULT_LANG)
    text = (m.text or "").strip()
    if not text:
        await m.answer(t("err_text_empty", lang))
        return
    if len(text) > 4000:
        await m.answer(t("err_text_too_long", lang))
        return

    await state.update_data(text=text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("support_skip_photo", lang), callback_data="sup_skip_photo")]
    ])
    await m.answer(t("support_ask_photo", lang), reply_markup=kb)
    await state.set_state(SupportFSM.awaiting_photo)


@router.message(SupportFSM.awaiting_photo, F.photo)
async def support_got_photo(m: Message, state: FSMContext, bot: Bot):
    photo = m.photo[-1]  # largest size
    await _finalize_request(m, state, bot, photo_file_id=photo.file_id)


@router.callback_query(SupportFSM.awaiting_photo, F.data == "sup_skip_photo")
async def support_skip_photo(cb: CallbackQuery, state: FSMContext, bot: Bot):
    await cb.answer()
    await cb.message.edit_reply_markup()
    # Synthesize a pseudo-message to reuse _finalize
    await _finalize_request(cb.message, state, bot, photo_file_id=None,
                             author_tg_id=cb.from_user.id)


@router.message(SupportFSM.awaiting_photo)
async def support_photo_hint(m: Message, state: FSMContext):
    """Any non-photo, non-callback message at this stage — gentle hint."""
    data = await state.get_data()
    lang = data.get("lang", DEFAULT_LANG)
    await m.answer(t("support_send_photo_hint", lang))


# ---------- Finalization: store + post to group ----------
async def _finalize_request(
    msg: Message,
    state: FSMContext,
    bot: Bot,
    photo_file_id: str | None,
    author_tg_id: int | None = None,
) -> None:
    data = await state.get_data()
    lang = data.get("lang", DEFAULT_LANG)
    category = data.get("category")
    text = data.get("text")

    if not category or not text:
        await state.clear()
        return

    tg_id = author_tg_id if author_tg_id is not None else msg.from_user.id

    group_chat_id = settings.get_support_chat_id(category)
    if group_chat_id is None:
        await msg.answer(t("support_group_not_configured", lang))
        await state.clear()
        return

    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if not user:
            await state.clear()
            return
        try:
            req = create_support_request(
                db, user, category=category, text=text, photo_file_id=photo_file_id,
            )
        except SupportError as e:
            log.warning("create_support_request failed: %s", e.code)
            await state.clear()
            return
        # Snapshot data while we still have session
        req_id = req.id
        short = _short_id(req_id)
        user_full_name = user.full_name or "—"
        user_phone = user.phone
        user_region = user.region.name_ru if user.region else "—"

    # Build group message (in RU by default; group members are staff)
    group_lang = "ru"
    body = t(
        "group_new_request", group_lang,
        short_id=short,
        cat_emoji=CATEGORY_EMOJI.get(category, ""),
        cat_name=_cat_label(category, group_lang),
        name=user_full_name,
        phone=user_phone,
        region=user_region,
        text=text,
    )
    kb = _build_group_kb(group_lang, request_open=True)

    # Post to group
    try:
        if photo_file_id:
            sent = await bot.send_photo(
                chat_id=group_chat_id,
                photo=photo_file_id,
                caption=body,
                reply_markup=kb,
            )
        else:
            sent = await bot.send_message(
                chat_id=group_chat_id,
                text=body,
                reply_markup=kb,
            )
    except Exception as e:
        log.exception("Failed to post support request to group %s: %s", group_chat_id, e)
        await msg.answer(t("support_group_not_configured", lang))
        await state.clear()
        return

    # Save group_chat_id / group_message_id on the request
    with SessionLocal() as db:
        attach_group_message(db, req_id, sent.chat.id, sent.message_id)

    await msg.answer(t("support_submitted", lang, short_id=short))
    await state.clear()


def _build_group_kb(lang: str, request_open: bool) -> InlineKeyboardMarkup | None:
    """Inline buttons shown under a group request message.

    'request_open' — True until an operator accepts it. After that we keep
    only the resolve/reject buttons.
    """
    if request_open:
        rows = [
            [
                InlineKeyboardButton(
                    text=t("group_btn_accept", lang), callback_data="sup_act:accept",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t("group_btn_resolve", lang), callback_data="sup_act:resolve",
                ),
                InlineKeyboardButton(
                    text=t("group_btn_reject", lang), callback_data="sup_act:reject",
                ),
            ],
        ]
    else:
        rows = [
            [
                InlineKeyboardButton(
                    text=t("group_btn_resolve", lang), callback_data="sup_act:resolve",
                ),
                InlineKeyboardButton(
                    text=t("group_btn_reject", lang), callback_data="sup_act:reject",
                ),
            ],
        ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ---------- Group-side callbacks (when operator presses a button) ----------
@router.callback_query(F.data.startswith("sup_act:"))
async def group_action(cb: CallbackQuery, bot: Bot):
    action = cb.data.split(":", 1)[1]
    if action not in ("accept", "in_progress", "resolve", "reject"):
        await cb.answer()
        return

    # Must be in a group (not a private DM)
    if cb.message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        await cb.answer()
        return

    with SessionLocal() as db:
        req = find_by_group_message(db, cb.message.chat.id, cb.message.message_id)
        if req is None:
            await cb.answer(t("group_already_closed", DEFAULT_LANG), show_alert=True)
            return
        if req.status in (SupportStatus.RESOLVED.value, SupportStatus.REJECTED.value):
            await cb.answer(t("group_already_closed", DEFAULT_LANG), show_alert=True)
            return

        # Who's acting — register/lookup user
        operator = db.query(User).filter(User.telegram_id == cb.from_user.id).first()
        if operator is None:
            # Allow group member to act even if not registered in the bot
            operator = User(
                telegram_id=cb.from_user.id,
                phone="group_member",
                full_name=cb.from_user.full_name or str(cb.from_user.id),
                region_id=req.user.region_id,  # placeholder
                role="admin",
                language="ru",
                qr_token=f"groupop-{cb.from_user.id}",
            )
            # Do NOT persist phantom user; just use their TG name in status
            operator_name = cb.from_user.full_name or str(cb.from_user.id)
        else:
            operator_name = operator.full_name or str(operator.telegram_id)

        new_status = {
            "accept": SupportStatus.ACCEPTED.value,
            "in_progress": SupportStatus.IN_PROGRESS.value,
            "resolve": SupportStatus.RESOLVED.value,
            "reject": SupportStatus.REJECTED.value,
        }[action]

        # Only transition if operator is persisted
        if operator.id is None:
            # Phantom operator: update status directly without resolver_id
            req.status = new_status
            if new_status in (SupportStatus.RESOLVED.value, SupportStatus.REJECTED.value):
                from datetime import datetime, timezone as _tz
                req.resolved_at = datetime.now(_tz.utc)
            db.commit()
            db.refresh(req)
        else:
            try:
                req = transition_status(db, req, new_status, operator)
            except SupportError as e:
                await cb.answer(e.code, show_alert=True)
                return

        # Snapshot for notification
        customer_tg_id = req.user.telegram_id
        customer_lang = req.user.language
        short = _short_id(req.id)
        category = req.category
        closed = new_status in (SupportStatus.RESOLVED.value, SupportStatus.REJECTED.value)
        resolved = new_status == SupportStatus.RESOLVED.value

    # Update message in group: append status badge, change buttons
    status_labels = {
        "accepted": t("group_status_accepted", "ru"),
        "in_progress": t("group_status_in_progress", "ru"),
        "resolved": t("group_status_resolved", "ru"),
        "rejected": t("group_status_rejected", "ru"),
    }
    status_text = t(
        "group_status_updated", "ru",
        status=status_labels.get(new_status, new_status),
        resolver_name=operator_name,
    )

    new_kb = None if closed else _build_group_kb("ru", request_open=False)

    try:
        if cb.message.caption is not None:
            # Photo message — update caption
            await bot.edit_message_caption(
                chat_id=cb.message.chat.id,
                message_id=cb.message.message_id,
                caption=(cb.message.caption or "") + status_text,
                reply_markup=new_kb,
            )
        else:
            await bot.edit_message_text(
                chat_id=cb.message.chat.id,
                message_id=cb.message.message_id,
                text=(cb.message.text or "") + status_text,
                reply_markup=new_kb,
            )
    except Exception as e:
        log.warning("group edit failed: %s", e)

    await cb.answer()

    # Notify customer if request was finalized
    if closed:
        category_label = t(f"support_cat_{category}", customer_lang)
        await notify_support_closed(
            telegram_id=customer_tg_id,
            category=category_label,
            short_id=short,
            resolved=resolved,
            note=None,
            lang=customer_lang,
        )


# ---------- /bind_support_group — helper for admins to discover chat IDs ----------
@router.message(Command("bind_support_group"))
async def bind_group(m: Message):
    """Used by admins in a group chat to see the chat_id they need to put in env."""
    if m.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        await m.answer(t("bind_group_not_in_group", DEFAULT_LANG))
        return
    parts = (m.text or "").split(maxsplit=1)
    if len(parts) < 2 or parts[1].strip() not in ("engineer", "complaint", "techsupport"):
        await m.answer(t("bind_group_usage", DEFAULT_LANG))
        return
    category = parts[1].strip()
    env_cat = {
        "engineer": "ENGINEER",
        "complaint": "COMPLAINT",
        "techsupport": "TECHSUPPORT",
    }[category]
    await m.answer(
        t("bind_group_shown", DEFAULT_LANG)
        .replace("{chat_id}", str(m.chat.id))
        .replace("{CAT}", env_cat),
    )
