"""Telegram bot entrypoint (long-polling worker)."""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from app.config import get_settings
from app.bot.handlers import customer, seller, admin as admin_handlers, support, contest
from app.db import SessionLocal
from app.services.exchange_rate import ensure_rate_fresh

settings = get_settings()
logging.basicConfig(level=settings.log_level)
log = logging.getLogger("delixi.bot")


async def refresh_rate_on_start() -> None:
    """Fetch today's USD rate from cbu.uz on bot startup.
    Runs in a thread so it doesn't block the event loop on slow network.
    """
    def _work():
        try:
            with SessionLocal() as db:
                rate = ensure_rate_fresh(db)
                log.info("USD rate on startup: %s UZS/USD", rate)
        except Exception as e:
            log.warning("refresh_rate_on_start failed: %s", e)
    await asyncio.to_thread(_work)


async def main():
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(customer.router)
    dp.include_router(seller.router)
    dp.include_router(admin_handlers.router)
    dp.include_router(support.router)
    dp.include_router(contest.router)

    log.info("DELIXI bot starting...")
    await refresh_rate_on_start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
