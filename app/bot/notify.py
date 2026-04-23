"""Outbound notifications from API to Telegram users.

Keeps a single shared Bot instance for fire-and-forget use from API handlers.
"""
import logging
from decimal import Decimal
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from app.config import get_settings

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
    """Format a number with thousand-separators using spaces."""
    q = n.quantize(Decimal("1")) if n == n.to_integral_value() else n
    s = f"{q:,}".replace(",", " ")
    return s


async def notify_purchase(
    telegram_id: int, amount: Decimal, bonus: Decimal, balance: Decimal
) -> None:
    text = (
        "✅ <b>Покупка подтверждена</b>\n\n"
        f"Сумма: <b>{_fmt(amount)}</b> сум\n"
        f"Начислено бонусов: <b>+{_fmt(bonus)}</b>\n"
        f"Баланс: <b>{_fmt(balance)}</b>"
    )
    try:
        await _get_bot().send_message(telegram_id, text)
    except Exception as e:
        log.warning("notify_purchase failed for %s: %s", telegram_id, e)


async def notify_redemption_approved(telegram_id: int, prize_name: str) -> None:
    try:
        await _get_bot().send_message(
            telegram_id,
            f"🎁 <b>Заявка на приз одобрена!</b>\n\n"
            f"Приз: <b>{prize_name}</b>\n"
            f"Вы можете забрать его в магазине.",
        )
    except Exception as e:
        log.warning("notify_redemption failed for %s: %s", telegram_id, e)


async def notify_redemption_rejected(
    telegram_id: int, prize_name: str, note: str | None
) -> None:
    extra = f"\n\nПричина: {note}" if note else ""
    try:
        await _get_bot().send_message(
            telegram_id,
            f"❌ <b>Заявка на «{prize_name}» отклонена.</b>"
            f"{extra}\n\nБонусы остались на вашем балансе.",
        )
    except Exception as e:
        log.warning("notify_redemption_reject failed for %s: %s", telegram_id, e)
