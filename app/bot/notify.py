"""Outbound notifications from API to Telegram users, localized."""
import logging
from decimal import Decimal
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from app.config import get_settings
from app.core.i18n import t, DEFAULT_LANG

log = logging.getLogger("delixi.notify")
_bot: Bot | None = None


def _get_bot() -> Bot:
    global _bot
    if _bot is None:
        _bot = Bot(
            token=get_settings().bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
    return _bot


def _fmt(n: Decimal) -> str:
    q = n.quantize(Decimal("1")) if n == n.to_integral_value() else n
    return f"{q:,}".replace(",", " ")


async def notify_purchase(
    telegram_id: int,
    amount: Decimal,
    bonus: Decimal,
    balance: Decimal,
    lang: str = DEFAULT_LANG,
) -> None:
    text = t(
        "notify_purchase", lang,
        amount=_fmt(amount),
        bonus=_fmt(bonus),
        balance=_fmt(balance),
    )
    try:
        await _get_bot().send_message(telegram_id, text)
    except Exception as e:
        log.warning("notify_purchase failed for %s: %s", telegram_id, e)


async def notify_redemption_approved(
    telegram_id: int, prize_name: str, lang: str = DEFAULT_LANG,
) -> None:
    try:
        await _get_bot().send_message(
            telegram_id,
            t("notify_redemption_approved", lang, prize=prize_name),
        )
    except Exception as e:
        log.warning("notify_redemption failed for %s: %s", telegram_id, e)


async def notify_redemption_rejected(
    telegram_id: int,
    prize_name: str,
    note: str | None,
    lang: str = DEFAULT_LANG,
) -> None:
    extra = t("rejection_reason", lang, note=note) if note else ""
    try:
        await _get_bot().send_message(
            telegram_id,
            t("notify_redemption_rejected", lang, prize=prize_name, extra=extra),
        )
    except Exception as e:
        log.warning("notify_redemption_reject failed for %s: %s", telegram_id, e)
