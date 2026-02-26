"""Точка входа: сборка бота, роутеры, graceful shutdown."""

import asyncio
import logging
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from bot.commands.start import router as start_router
from bot.handlers.callbacks import router as callbacks_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def on_global_error(event: object, exception: Exception) -> None:
    """Глобальный обработчик ошибок: логируем и не роняем бота."""
    logger.exception("Unhandled error: %s", exception)


def main() -> None:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN is not set")
        sys.exit(1)

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(callbacks_router)
    dp.errors.register(on_global_error)

    async def run() -> None:
        try:
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        finally:
            await bot.session.close()

    try:
        asyncio.run(run())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown requested, stopping bot...")


if __name__ == "__main__":
    main()
