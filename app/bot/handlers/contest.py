"""Contest handlers: client submits a work, judges score it 5×10.

Client FSM (in DM with bot):
    ContestSubmit.awaiting_photo → awaiting_description → done

Judge FSM (in DM — triggered by clicking a button in the judges group):
    ContestScore.c1 → c2 → c3 → c4 → c5 → done
"""
import logging
import uuid
from decimal import Decimal
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
from app.models import (
    User, UserRole, Contest, ContestWork, WorkStatus,
)
from app.services.contest import (
    get_active_contest, start_contest, end_contest, leaderboard,
    submit_work, attach_group_message, find_by_group_message,
    submit_score, count_judges, count_scores, average_so_far,
    finalize_if_complete, ContestError,
)

log = logging.getLogger("delixi.bot.contest")
router = Router()
settings = get_settings()


# ---------- FSM ----------
class ContestSubmit(StatesGroup):
    awaiting_photo = State()
    awaiting_description = State()


class ContestScoreFSM(StatesGroup):
    c1 = State()
    c2 = State()
    c3 = State()
    c4 = State()
    c5 = State()


# ---------- Helpers ----------
def _in_any(key: str):
    texts = {t(key, lang) for lang in SUPPORTED_LANGS}
    return F.text.in_(texts)


def _short(u) -> str:
    return str(u).replace("-", "")[:6].upper()


def _is_admin(tg_id: int) -> bool:
    if tg_id in settings.admin_tg_id_set:
        return True
    with SessionLocal() as db:
        u = db.query(User).filter(User.telegram_id == tg_id).first()
        return bool(u and u.role == UserRole.ADMIN.value)


def _score_kb(state_tag: str) -> InlineKeyboardMarkup:
    """1-10 grid for scoring."""
    row1 = [
        InlineKeyboardButton(text=str(i), callback_data=f"csc:{state_tag}:{i}")
        for i in range(1, 6)
    ]
    row2 = [
        InlineKeyboardButton(text=str(i), callback_data=f"csc:{state_tag}:{i}")
        for i in range(6, 11)
    ]
    return InlineKeyboardMarkup(inline_keyboard=[row1, row2])


# ==============================================================
# CLIENT SIDE — submit a work
# ==============================================================
@router.message(_in_any("menu_contest"))
async def contest_entry(m: Message, state: FSMContext):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == m.from_user.id).first()
        if not user:
            await m.answer(t("not_registered", DEFAULT_LANG))
            return
        lang = user.language
        contest = get_active_contest(db)
        if contest is None:
            await m.answer(t("contest_none_active", lang))
            return
        name = contest.name
        description = contest.description or ""

    await state.clear()
    text = t("contest_info", lang, name=name, description=description)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=t("contest_submit_btn", lang),
            callback_data="contest_submit",
        )
    ]])
    await m.answer(text, reply_markup=kb)


@router.callback_query(F.data == "contest_submit")
async def contest_submit_start(cb: CallbackQuery, state: FSMContext):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == cb.from_user.id).first()
        lang = user.language if user else DEFAULT_LANG
        contest = get_active_contest(db)
        if contest is None:
            await cb.answer(t("contest_none_active", lang), show_alert=True)
            return

    await state.update_data(lang=lang, contest_id=str(contest.id))
    await cb.answer()
    await cb.message.edit_reply_markup()
    await cb.message.answer(t("contest_ask_photo", lang))
    await state.set_state(ContestSubmit.awaiting_photo)


@router.message(ContestSubmit.awaiting_photo, F.photo)
async def contest_got_photo(m: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", DEFAULT_LANG)
    photo = m.photo[-1]  # largest
    await state.update_data(photo_file_id=photo.file_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=t("contest_skip_description", lang),
            callback_data="contest_skip_desc",
        )
    ]])
    await m.answer(t("contest_ask_description", lang), reply_markup=kb)
    await state.set_state(ContestSubmit.awaiting_description)


@router.message(ContestSubmit.awaiting_photo)
async def contest_photo_hint(m: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", DEFAULT_LANG)
    await m.answer(t("contest_photo_hint", lang))


@router.message(ContestSubmit.awaiting_description, F.text)
async def contest_got_description(m: Message, state: FSMContext, bot: Bot):
    description = (m.text or "").strip()
    if len(description) > 2000:
        data = await state.get_data()
        lang = data.get("lang", DEFAULT_LANG)
        await m.answer(t("contest_description_too_long", lang))
        return
    await _finalize_submission(m, state, bot, description=description)


@router.callback_query(ContestSubmit.awaiting_description, F.data == "contest_skip_desc")
async def contest_skip_description(cb: CallbackQuery, state: FSMContext, bot: Bot):
    await cb.answer()
    await cb.message.edit_reply_markup()
    await _finalize_submission(cb.message, state, bot, description=None,
                                 author_tg_id=cb.from_user.id)


async def _finalize_submission(
    msg: Message, state: FSMContext, bot: Bot,
    description: str | None, author_tg_id: int | None = None,
) -> None:
    data = await state.get_data()
    lang = data.get("lang", DEFAULT_LANG)
    photo_file_id = data.get("photo_file_id")
    contest_id = data.get("contest_id")

    if not photo_file_id or not contest_id:
        await state.clear()
        return

    tg_id = author_tg_id if author_tg_id is not None else msg.from_user.id

    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if not user:
            await state.clear()
            return
        contest = get_active_contest(db)
        if contest is None:
            await msg.answer(t("contest_none_active", lang))
            await state.clear()
            return
        judge_chat_id = contest.judge_chat_id
        try:
            work = submit_work(
                db, user=user, contest=contest,
                photo_file_id=photo_file_id, description=description,
            )
        except ContestError as e:
            log.warning("submit_work failed: %s", e.code)
            await state.clear()
            return
        work_id = work.id
        short = _short(work_id)
        user_name = user.full_name or "—"
        user_phone = user.phone
        user_region = user.region.name_ru if user.region else "—"
        total_judges = count_judges(db)

    if not judge_chat_id:
        # No judge group configured — contest can't really work
        await msg.answer(t("contest_judges_unavailable", lang))
        await state.clear()
        return

    # Post the work into the judges group
    group_lang = "ru"
    caption = t(
        "group_new_work", group_lang,
        short_id=short,
        name=user_name,
        phone=user_phone,
        region=user_region,
        description=description or "—",
        scored=0,
        total=total_judges,
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=t("group_btn_score", group_lang),
            callback_data=f"cwk_start:{work_id}",
        )
    ]])
    try:
        sent = await bot.send_photo(
            chat_id=judge_chat_id,
            photo=photo_file_id,
            caption=caption,
            reply_markup=kb,
        )
    except Exception as e:
        log.exception("Failed to post work to judges group %s: %s", judge_chat_id, e)
        await msg.answer(t("contest_judges_unavailable", lang))
        await state.clear()
        return

    with SessionLocal() as db:
        attach_group_message(db, work_id, sent.chat.id, sent.message_id)

    await msg.answer(t("contest_submitted", lang, short_id=short))
    await state.clear()


# ==============================================================
# JUDGE SIDE — scoring FSM (starts from group button)
# ==============================================================
@router.callback_query(F.data.startswith("cwk_start:"))
async def judge_start_scoring(cb: CallbackQuery, state: FSMContext, bot: Bot):
    """Judge tapped ⭐ in the group. Begin a private DM scoring session."""
    work_id = cb.data.split(":", 1)[1]
    with SessionLocal() as db:
        work = db.get(ContestWork, work_id)
        if work is None:
            await cb.answer(t("contest_work_not_found", DEFAULT_LANG), show_alert=True)
            return
        judge = db.query(User).filter(User.telegram_id == cb.from_user.id).first()
        if judge is None or judge.role != UserRole.JUDGE.value:
            await cb.answer(t("contest_not_a_judge", DEFAULT_LANG), show_alert=True)
            return
        judge_lang = judge.language
        # Check if already scored
        from app.models import ContestScore
        prev = (
            db.query(ContestScore)
            .filter(
                ContestScore.work_id == work.id,
                ContestScore.judge_id == judge.id,
            )
            .first()
        )
        if prev is not None:
            await cb.answer(t("contest_already_scored", judge_lang), show_alert=True)
            return

    await cb.answer()
    # Open private DM with the judge
    try:
        await bot.send_message(
            chat_id=cb.from_user.id,
            text=t("score_start", judge_lang, work_short=_short(work_id)),
        )
        # Ask first criterion
        await bot.send_message(
            chat_id=cb.from_user.id,
            text=t("score_ask_c1", judge_lang),
            reply_markup=_score_kb("1"),
        )
    except Exception as e:
        log.warning("Could not DM judge %s: %s", cb.from_user.id, e)
        await cb.answer(t("score_open_dm_first", judge_lang), show_alert=True)
        return

    await state.set_state(ContestScoreFSM.c1)
    await state.update_data(
        work_id=work_id, lang=judge_lang, c1=None, c2=None, c3=None, c4=None, c5=None,
    )


async def _score_step(
    cb: CallbackQuery, state: FSMContext, bot: Bot,
    current_key: str, next_state: State | None, next_key_prompt: str | None,
    next_tag: str | None,
) -> None:
    """Generic advance-to-next-criterion helper."""
    _, state_tag, value = cb.data.split(":", 2)
    value = int(value)
    data = await state.get_data()
    lang = data.get("lang", DEFAULT_LANG)

    await state.update_data(**{current_key: value})
    await cb.answer()
    await cb.message.edit_reply_markup()  # remove old buttons

    if next_state and next_key_prompt and next_tag:
        await bot.send_message(
            chat_id=cb.from_user.id,
            text=t(next_key_prompt, lang),
            reply_markup=_score_kb(next_tag),
        )
        await state.set_state(next_state)
    else:
        # Final step — persist the score
        await _finalize_score(cb, state, bot)


@router.callback_query(ContestScoreFSM.c1, F.data.startswith("csc:1:"))
async def score_c1(cb: CallbackQuery, state: FSMContext, bot: Bot):
    await _score_step(
        cb, state, bot, "c1", ContestScoreFSM.c2, "score_ask_c2", "2",
    )


@router.callback_query(ContestScoreFSM.c2, F.data.startswith("csc:2:"))
async def score_c2(cb: CallbackQuery, state: FSMContext, bot: Bot):
    await _score_step(
        cb, state, bot, "c2", ContestScoreFSM.c3, "score_ask_c3", "3",
    )


@router.callback_query(ContestScoreFSM.c3, F.data.startswith("csc:3:"))
async def score_c3(cb: CallbackQuery, state: FSMContext, bot: Bot):
    await _score_step(
        cb, state, bot, "c3", ContestScoreFSM.c4, "score_ask_c4", "4",
    )


@router.callback_query(ContestScoreFSM.c4, F.data.startswith("csc:4:"))
async def score_c4(cb: CallbackQuery, state: FSMContext, bot: Bot):
    await _score_step(
        cb, state, bot, "c4", ContestScoreFSM.c5, "score_ask_c5", "5",
    )


@router.callback_query(ContestScoreFSM.c5, F.data.startswith("csc:5:"))
async def score_c5(cb: CallbackQuery, state: FSMContext, bot: Bot):
    await _score_step(cb, state, bot, "c5", None, None, None)


async def _finalize_score(cb: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    lang = data.get("lang", DEFAULT_LANG)
    work_id = data.get("work_id")

    c1, c2, c3, c4, c5 = (data[k] for k in ("c1", "c2", "c3", "c4", "c5"))

    with SessionLocal() as db:
        work = db.get(ContestWork, work_id)
        if work is None:
            await bot.send_message(cb.from_user.id, t("contest_work_not_found", lang))
            await state.clear()
            return
        judge = db.query(User).filter(User.telegram_id == cb.from_user.id).first()
        try:
            submit_score(db, work, judge, c1, c2, c3, c4, c5)
        except ContestError as e:
            await bot.send_message(
                cb.from_user.id, t(f"score_err_{e.code}", lang)
                if t(f"score_err_{e.code}", lang) != f"score_err_{e.code}"
                else e.code
            )
            await state.clear()
            return
        my_avg = (c1 + c2 + c3 + c4 + c5) / 5.0
        # Refresh to get updated scoring progress
        db.refresh(work)
        scored = count_scores(db, work)
        total_judges = count_judges(db)
        just_finalized = finalize_if_complete(db, work)
        if just_finalized:
            db.refresh(work)
        work_short = _short(work.id)
        customer_tg_id = work.user.telegram_id
        customer_lang = work.user.language
        customer_name = work.user.full_name or "—"
        current_avg = work.average_score if just_finalized else average_so_far(db, work)
        group_chat_id = work.group_chat_id
        group_message_id = work.group_message_id
        description = work.description or "—"
        user_phone = work.user.phone
        user_region = work.user.region.name_ru if work.user.region else "—"

    # Confirm to judge
    await bot.send_message(
        cb.from_user.id,
        t("score_saved", lang, avg=f"{my_avg:.1f}"),
    )
    await state.clear()

    # Update group message caption with new progress / finalization
    if group_chat_id and group_message_id:
        try:
            if just_finalized:
                new_caption = t(
                    "group_work_finalized", "ru",
                    short_id=work_short, name=customer_name,
                    phone=user_phone, region=user_region,
                    description=description,
                    avg=f"{current_avg}",
                )
                new_kb = None
            else:
                new_caption = t(
                    "group_new_work", "ru",
                    short_id=work_short, name=customer_name,
                    phone=user_phone, region=user_region,
                    description=description,
                    scored=scored, total=total_judges,
                )
                new_kb = InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=t("group_btn_score", "ru"),
                        callback_data=f"cwk_start:{work_id}",
                    )
                ]])
            await bot.edit_message_caption(
                chat_id=group_chat_id,
                message_id=group_message_id,
                caption=new_caption,
                reply_markup=new_kb,
            )
        except Exception as e:
            log.warning("group edit failed: %s", e)

    # Notify customer when finalized
    if just_finalized:
        try:
            await bot.send_message(
                customer_tg_id,
                t("notify_contest_finalized", customer_lang,
                   short_id=work_short, avg=f"{current_avg}"),
            )
        except Exception as e:
            log.warning("customer notify failed: %s", e)


# ==============================================================
# ADMIN COMMANDS
# ==============================================================
@router.message(Command("start_contest"))
async def cmd_start_contest(m: Message):
    if not _is_admin(m.from_user.id):
        return
    # Command usage: /start_contest Name of contest | Optional description
    raw = (m.text or "").split(maxsplit=1)
    if len(raw) < 2:
        await m.answer(t("contest_cmd_usage", DEFAULT_LANG))
        return
    payload = raw[1]
    parts = payload.split("|", 1)
    name = parts[0].strip()
    description = parts[1].strip() if len(parts) == 2 else None
    if not name:
        await m.answer(t("contest_cmd_usage", DEFAULT_LANG))
        return

    # Use judge_chat_id = same chat where command sent (if group), else None
    judge_chat_id = m.chat.id if m.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP) else None

    with SessionLocal() as db:
        contest = start_contest(
            db, name=name, description=description, judge_chat_id=judge_chat_id,
        )
    msg = t(
        "contest_started", DEFAULT_LANG,
        name=contest.name, judges_chat=str(judge_chat_id or "—"),
    )
    await m.answer(msg)


@router.message(Command("end_contest"))
async def cmd_end_contest(m: Message, bot: Bot):
    if not _is_admin(m.from_user.id):
        return
    with SessionLocal() as db:
        contest = end_contest(db)
        if contest is None:
            await m.answer(t("contest_none_active", DEFAULT_LANG))
            return
        top = leaderboard(db, contest, limit=10)
        lines = [t("contest_results_header", DEFAULT_LANG, name=contest.name)]
        if not top:
            lines.append(t("contest_results_empty", DEFAULT_LANG))
        else:
            for i, w in enumerate(top, 1):
                lines.append(
                    t("contest_results_line", DEFAULT_LANG,
                      place=i,
                      name=(w.user.full_name or str(w.user.telegram_id)),
                      avg=f"{w.average_score or 0}",
                    )
                )
    await m.answer("\n".join(lines))


@router.message(Command("make_judge"))
async def cmd_make_judge(m: Message):
    if not _is_admin(m.from_user.id):
        return
    parts = (m.text or "").split()
    if len(parts) != 2:
        await m.answer(t("make_judge_usage", DEFAULT_LANG))
        return
    try:
        tg_id = int(parts[1])
    except ValueError:
        await m.answer(t("make_seller_id_must_be_number", DEFAULT_LANG))
        return
    with SessionLocal() as db:
        u = db.query(User).filter(User.telegram_id == tg_id).first()
        if not u:
            await m.answer(
                t("user_not_found_ask_start", DEFAULT_LANG, tg_id=tg_id)
            )
            return
        u.role = UserRole.JUDGE.value
        u.is_active = True
        db.commit()
        name = u.full_name or str(tg_id)
    await m.answer(t("made_judge", DEFAULT_LANG, name=name))


@router.message(Command("judges"))
async def cmd_list_judges(m: Message):
    if not _is_admin(m.from_user.id):
        return
    with SessionLocal() as db:
        rows = (
            db.query(User)
            .filter(User.role == UserRole.JUDGE.value)
            .order_by(User.created_at.desc())
            .all()
        )
        items = [(u.telegram_id, u.full_name or "—", "✅" if u.is_active else "⛔")
                 for u in rows]
    if not items:
        await m.answer(t("judges_empty", DEFAULT_LANG))
        return
    lines = [t("judges_header", DEFAULT_LANG)]
    for tg_id, name, active in items:
        lines.append(f"{active} <code>{tg_id}</code> — {name}")
    await m.answer("\n".join(lines))
