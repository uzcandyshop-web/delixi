"""Admin handlers: inline-keyboard panel + redemption approval, seller management.

The admin opens /admin and sees a 2-column inline keyboard with all common
actions. Commands without parameters are wired to direct callbacks. Commands
that need parameters (make_seller, make_judge, start_contest) show a usage
template the admin can copy and edit.
"""
import logging
from decimal import Decimal
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    BufferedInputFile,
)

from app.config import get_settings
from app.core.i18n import t, DEFAULT_LANG
from app.core.chart import make_daily_chart
from app.db import SessionLocal
from app.models import User, Redemption, UserRole, Region
from app.services.redemptions import (
    approve_redemption, reject_redemption, RedemptionError,
)
from app.services.exchange_rate import (
    get_current_rate, update_daily_rate,
)
from app.services.contest import (
    end_contest, leaderboard, get_active_contest,
)
from app.services.reports import admin_report, admin_by_region
from app.bot.notify import (
    notify_redemption_approved, notify_redemption_rejected,
)

log = logging.getLogger("delixi.bot.admin")
router = Router()
settings = get_settings()


# ---------- Helpers ----------
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


def _admin_panel_kb(lang: str) -> InlineKeyboardMarkup:
    """The main admin inline keyboard — 2 columns, ~10 buttons."""
    return InlineKeyboardMarkup(inline_keyboard=[
        # Row 1: redemptions
        [
            InlineKeyboardButton(
                text=t("adm_btn_pending", lang), callback_data="ap:pending",
            ),
        ],
        # Row 2: people
        [
            InlineKeyboardButton(
                text=t("adm_btn_sellers", lang), callback_data="ap:sellers",
            ),
            InlineKeyboardButton(
                text=t("adm_btn_judges", lang), callback_data="ap:judges",
            ),
        ],
        # Row 3: assignment templates
        [
            InlineKeyboardButton(
                text=t("adm_btn_make_seller", lang), callback_data="ap:make_seller",
            ),
            InlineKeyboardButton(
                text=t("adm_btn_make_judge", lang), callback_data="ap:make_judge",
            ),
        ],
        # Row 4: rate
        [
            InlineKeyboardButton(
                text=t("adm_btn_rate", lang), callback_data="ap:rate",
            ),
            InlineKeyboardButton(
                text=t("adm_btn_update_rate", lang), callback_data="ap:update_rate",
            ),
        ],
        # Row 5: contest
        [
            InlineKeyboardButton(
                text=t("adm_btn_start_contest", lang), callback_data="ap:start_contest",
            ),
            InlineKeyboardButton(
                text=t("adm_btn_end_contest", lang), callback_data="ap:end_contest",
            ),
        ],
        # Row 6: report
        [
            InlineKeyboardButton(
                text=t("adm_btn_report", lang), callback_data="ap:report",
            ),
        ],
    ])


def _back_to_panel_kb(lang: str) -> InlineKeyboardMarkup:
    """Single 'back to panel' button — used after a one-shot action."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=t("adm_btn_back", lang), callback_data="ap:home",
        )
    ]])


# ==============================================================
# /admin entrypoint
# ==============================================================
@router.message(Command("admin"))
async def admin_menu(m: Message):
    if not _is_admin(m.from_user.id):
        return
    lang = _admin_lang(m.from_user.id)
    await m.answer(
        t("adm_panel_title", lang), reply_markup=_admin_panel_kb(lang),
    )


@router.callback_query(F.data == "ap:home")
async def back_home(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer()
        return
    lang = _admin_lang(cb.from_user.id)
    await cb.answer()
    await cb.message.edit_text(
        t("adm_panel_title", lang), reply_markup=_admin_panel_kb(lang),
    )


# ==============================================================
# Pending redemptions
# ==============================================================
@router.callback_query(F.data == "ap:pending")
async def panel_pending(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer()
        return
    lang = _admin_lang(cb.from_user.id)
    await cb.answer()
    await _send_pending(cb.message, lang)


@router.message(Command("pending"))
async def list_pending(m: Message):
    if not _is_admin(m.from_user.id):
        return
    lang = _admin_lang(m.from_user.id)
    await _send_pending(m, lang)


async def _send_pending(target_msg: Message, lang: str) -> None:
    with SessionLocal() as db:
        rows = (
            db.query(Redemption)
            .filter(Redemption.status == "pending")
            .order_by(Redemption.requested_at)
            .limit(20)
            .all()
        )
        items = [
            (r.id, r.prize.name, r.cost_bonus,
             r.user.full_name or str(r.user.telegram_id))
            for r in rows
        ]

    if not items:
        await target_msg.answer(t("no_pending", lang), reply_markup=_back_to_panel_kb(lang))
        return

    for red_id, prize_name, cost, customer_name in items:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=t("approve_btn", lang), callback_data=f"adm:approve:{red_id}"),
            InlineKeyboardButton(text=t("reject_btn", lang), callback_data=f"adm:reject:{red_id}"),
        ]])
        await target_msg.answer(
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


# ==============================================================
# Sellers list
# ==============================================================
@router.callback_query(F.data == "ap:sellers")
async def panel_sellers(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer()
        return
    lang = _admin_lang(cb.from_user.id)
    await cb.answer()
    await _send_sellers(cb.message, lang)


@router.message(Command("sellers"))
async def list_sellers(m: Message):
    if not _is_admin(m.from_user.id):
        return
    lang = _admin_lang(m.from_user.id)
    await _send_sellers(m, lang)


async def _send_sellers(target_msg: Message, lang: str) -> None:
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
        await target_msg.answer(
            t("sellers_empty", lang), reply_markup=_back_to_panel_kb(lang),
        )
        return
    lines = [t("sellers_header", lang)]
    for tg_id, name, region, active in items:
        lines.append(f"{active} <code>{tg_id}</code> — {name} ({region})")
    await target_msg.answer("\n".join(lines), reply_markup=_back_to_panel_kb(lang))


# ==============================================================
# Judges list
# ==============================================================
@router.callback_query(F.data == "ap:judges")
async def panel_judges(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer()
        return
    lang = _admin_lang(cb.from_user.id)
    await cb.answer()
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
        await cb.message.answer(
            t("judges_empty", lang), reply_markup=_back_to_panel_kb(lang),
        )
        return
    lines = [t("judges_header", lang)]
    for tg_id, name, active in items:
        lines.append(f"{active} <code>{tg_id}</code> — {name}")
    await cb.message.answer("\n".join(lines), reply_markup=_back_to_panel_kb(lang))


# ==============================================================
# Assignment commands (with parameters) — show template
# ==============================================================
@router.callback_query(F.data == "ap:make_seller")
async def panel_make_seller(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer()
        return
    lang = _admin_lang(cb.from_user.id)
    await cb.answer()
    # Show usage + list of region codes
    with SessionLocal() as db:
        regions = (
            db.query(Region)
            .filter(Region.is_active.is_(True))
            .order_by(Region.code)
            .all()
        )
        region_lines = [f"  • <code>{r.code}</code> — {r.name_ru}" for r in regions]
    text = t("make_seller_usage", lang) + "\n\n" + t("regions_available", lang) + "\n" + "\n".join(region_lines)
    await cb.message.answer(text, reply_markup=_back_to_panel_kb(lang))


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


@router.callback_query(F.data == "ap:make_judge")
async def panel_make_judge(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer()
        return
    lang = _admin_lang(cb.from_user.id)
    await cb.answer()
    await cb.message.answer(
        t("make_judge_usage", lang), reply_markup=_back_to_panel_kb(lang),
    )


# ==============================================================
# Exchange rate
# ==============================================================
@router.callback_query(F.data == "ap:rate")
async def panel_rate(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer()
        return
    lang = _admin_lang(cb.from_user.id)
    await cb.answer()
    with SessionLocal() as db:
        rate = get_current_rate(db)
    await cb.message.answer(
        t("rate_current", lang, rate=_fmt(rate)),
        reply_markup=_back_to_panel_kb(lang),
    )


@router.message(Command("rate"))
async def cmd_rate(m: Message):
    if not _is_admin(m.from_user.id):
        return
    lang = _admin_lang(m.from_user.id)
    with SessionLocal() as db:
        rate = get_current_rate(db)
    await m.answer(t("rate_current", lang, rate=_fmt(rate)))


@router.callback_query(F.data == "ap:update_rate")
async def panel_update_rate(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer()
        return
    lang = _admin_lang(cb.from_user.id)
    await cb.answer()
    await cb.message.answer(t("rate_updating", lang))
    with SessionLocal() as db:
        new_rate = update_daily_rate(db)
    if new_rate is None:
        await cb.message.answer(
            t("rate_update_failed", lang), reply_markup=_back_to_panel_kb(lang),
        )
    else:
        await cb.message.answer(
            t("rate_updated", lang, rate=_fmt(new_rate)),
            reply_markup=_back_to_panel_kb(lang),
        )


@router.message(Command("update_rate"))
async def cmd_update_rate(m: Message):
    if not _is_admin(m.from_user.id):
        return
    lang = _admin_lang(m.from_user.id)
    await m.answer(t("rate_updating", lang))
    with SessionLocal() as db:
        new_rate = update_daily_rate(db)
    if new_rate is None:
        await m.answer(t("rate_update_failed", lang))
    else:
        await m.answer(t("rate_updated", lang, rate=_fmt(new_rate)))


# ==============================================================
# Contest
# ==============================================================
@router.callback_query(F.data == "ap:start_contest")
async def panel_start_contest(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer()
        return
    lang = _admin_lang(cb.from_user.id)
    await cb.answer()
    await cb.message.answer(
        t("contest_cmd_usage", lang), reply_markup=_back_to_panel_kb(lang),
    )


@router.callback_query(F.data == "ap:end_contest")
async def panel_end_contest(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer()
        return
    lang = _admin_lang(cb.from_user.id)
    await cb.answer()
    with SessionLocal() as db:
        # Check if there's an active contest
        active = get_active_contest(db)
        if active is None:
            await cb.message.answer(
                t("contest_none_active", lang), reply_markup=_back_to_panel_kb(lang),
            )
            return
        # Confirm before ending
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=t("adm_confirm_end_contest", lang),
                callback_data="ap:end_contest_confirm",
            )
        ],
        [
            InlineKeyboardButton(
                text=t("adm_btn_back", lang), callback_data="ap:home",
            )
        ],
    ])
    await cb.message.answer(
        t("adm_confirm_end_contest_q", lang, name=active.name),
        reply_markup=kb,
    )


@router.callback_query(F.data == "ap:end_contest_confirm")
async def panel_end_contest_confirm(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer()
        return
    lang = _admin_lang(cb.from_user.id)
    await cb.answer()
    await cb.message.edit_reply_markup()

    with SessionLocal() as db:
        contest = end_contest(db)
        if contest is None:
            await cb.message.answer(
                t("contest_none_active", lang), reply_markup=_back_to_panel_kb(lang),
            )
            return
        top = leaderboard(db, contest, limit=10)
        lines = [t("contest_results_header", lang, name=contest.name)]
        if not top:
            lines.append(t("contest_results_empty", lang))
        else:
            for i, w in enumerate(top, 1):
                lines.append(
                    t("contest_results_line", lang,
                      place=i,
                      name=(w.user.full_name or str(w.user.telegram_id)),
                      avg=f"{w.average_score or 0}",
                    )
                )
    await cb.message.answer("\n".join(lines), reply_markup=_back_to_panel_kb(lang))


# ==============================================================
# Reports — period picker
# ==============================================================
def _admin_periods_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("rep_today", lang), callback_data="rep:a:today"),
        InlineKeyboardButton(text=t("rep_week", lang), callback_data="rep:a:week"),
        InlineKeyboardButton(text=t("rep_month", lang), callback_data="rep:a:month"),
    ], [
        InlineKeyboardButton(text=t("adm_btn_back", lang), callback_data="ap:home"),
    ]])


@router.callback_query(F.data == "ap:report")
async def panel_report(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        await cb.answer()
        return
    lang = _admin_lang(cb.from_user.id)
    await cb.answer()
    await cb.message.answer(
        t("rep_choose_period", lang), reply_markup=_admin_periods_kb(lang),
    )


@router.message(Command("report"))
async def cmd_report(m: Message):
    if not _is_admin(m.from_user.id):
        return
    lang = _admin_lang(m.from_user.id)
    await m.answer(t("rep_choose_period", lang), reply_markup=_admin_periods_kb(lang))


@router.callback_query(F.data.startswith("rep:a:"))
async def admin_report_cb(cb: CallbackQuery):
    period = cb.data.split(":", 2)[2]
    if period not in ("today", "week", "month"):
        await cb.answer()
        return
    if not _is_admin(cb.from_user.id):
        await cb.answer()
        return
    lang = _admin_lang(cb.from_user.id)

    with SessionLocal() as db:
        report = admin_report(db, period)
        regions = admin_by_region(db, period)

    await cb.answer()
    await cb.message.edit_reply_markup()

    if report.count == 0:
        await cb.message.answer(
            t(f"rep_admin_empty_{period}", lang),
            reply_markup=_back_to_panel_kb(lang),
        )
        return

    # Text summary
    summary = t(
        "rep_admin_summary", lang,
        period=t(f"rep_period_label_{period}", lang),
        count=report.count,
        total=_fmt(report.total),
        bonus=_fmt(report.bonus),
        avg=_fmt(report.avg_check),
    )
    if regions:
        lines = [summary, "", t("report_by_region", lang)]
        for name, count, rev in regions:
            lines.append(f"  • {name}: {count} тр., {_fmt(rev)} сум")
        await cb.message.answer("\n".join(lines))
    else:
        await cb.message.answer(summary)

    # Chart for week/month
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
            reply_markup=_back_to_panel_kb(lang),
        )
    else:
        # Today — just attach back button to last text
        await cb.message.answer(t("rep_done", lang), reply_markup=_back_to_panel_kb(lang))
