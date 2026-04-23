"""Telegram bot entrypoint (long-polling worker)."""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from app.config import get_settings
from app.bot.handlers import customer, seller, admin as admin_handlers

settings = get_settings()
logging.basicConfig(level=settings.log_level)
log = logging.getLogger("delixi.bot")


async def main():
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(customer.router)
    dp.include_router(seller.router)
    dp.include_router(admin_handlers.router)

    log.info("DELIXI bot starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
