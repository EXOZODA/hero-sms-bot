"""
Точка входа. Загружает app из src.app_setup и запускает сервер.

Render: python main.py (webhook, прод)
Локально: python main.py --polling (polling, тест)
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def start_polling():
    """Запуск в режиме polling (для локальной разработки)."""
    from src.config import Config
    from aiogram import Bot
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    from src.bot.handlers import router as bot_router
    from src.bot.middlewares import ErrorHandlingMiddleware, RateLimitMiddleware, UserMiddleware
    from aiogram import Dispatcher
    from aiogram.fsm.storage.memory import MemoryStorage

    config = Config()
    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(bot_router)
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())
    dp.message.middleware(RateLimitMiddleware(rate_limit=1.0))
    dp.callback_query.middleware(RateLimitMiddleware(rate_limit=1.0))
    dp.message.middleware(ErrorHandlingMiddleware())
    dp.callback_query.middleware(ErrorHandlingMiddleware())

    logger.info("Удаляю webhook для polling...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as exc:
        logger.warning(f"Ошибка: {exc}")

    logger.info("Бот запущен в режиме polling! Нажмите Ctrl+C для остановки.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    if "--polling" in sys.argv or "-p" in sys.argv:
        asyncio.run(start_polling())
    else:
        import uvicorn
        from src.config import Config

        config = Config()
        logger.info(f"Запуск webhook сервера на {config.WEBAPP_HOST}:{config.WEBAPP_PORT}")

        uvicorn.run(
            "src.app_setup:app",
            host=config.WEBAPP_HOST,
            port=config.WEBAPP_PORT,
            reload=False,
            log_level="info",
        )
