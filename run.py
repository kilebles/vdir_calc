import asyncio
import logging

from aiogram import Bot, Dispatcher

from app import (
    CONFIG,
    set_default_commands,
    register_handlers,
    init_db,
    start_scheduler,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def main() -> None:
    await init_db()
    bot = Bot(token=CONFIG.TELEGRAM_TOKEN)
    dp = Dispatcher()

    logger.info("Start bot")
    await set_default_commands(bot)
    await register_handlers(dp)
    start_scheduler(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
