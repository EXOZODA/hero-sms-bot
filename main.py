"""
Точка входа в бота. Webhook режим для деплоя на Render/Vercel/etc.
Поддерживает также polling-режим для локальной разработки.
"""

import logging
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path для корректного импорта
sys.path.insert(0, str(Path(__file__).parent))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.bot.handlers import router as bot_router
from src.bot.middlewares import (
    ErrorHandlingMiddleware,
    RateLimitMiddleware,
    UserMiddleware,
)
from src.config import Config

# ─── Настройка логирования ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── Конфиг ────────────────────────────────────────────────────────────

config = Config()

if not config.BOT_TOKEN:
    logger.error("BOT_TOKEN не указан! Проверьте .env файл.")
    sys.exit(1)

# ─── Инициализация бота ────────────────────────────────────────────────

bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Подключаем роутер
dp.include_router(bot_router)

# Регистрируем middleware
dp.message.middleware(UserMiddleware())
dp.callback_query.middleware(UserMiddleware())
dp.message.middleware(RateLimitMiddleware(rate_limit=1.0))
dp.callback_query.middleware(RateLimitMiddleware(rate_limit=1.0))
dp.message.middleware(ErrorHandlingMiddleware())
dp.callback_query.middleware(ErrorHandlingMiddleware())

# ─── FastAPI приложение (Webhook) ──────────────────────────────────────

app = FastAPI(title="HeroSMS Bot")


@app.on_event("startup")
async def on_startup():
    """Устанавливает webhook при запуске."""
    webhook_url = config.webhook_full_url
    logger.info(f"Устанавливаю webhook: {webhook_url}")

    try:
        kwargs = {}
        if config.WEBHOOK_SECRET_TOKEN:
            kwargs["secret_token"] = config.WEBHOOK_SECRET_TOKEN
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"],
            **kwargs,
        )
        webhook_info = await bot.get_webhook_info()
        logger.info(f"Webhook установлен: {webhook_info.url}")
    except Exception as exc:
        logger.error(f"Не удалось установить webhook: {exc}")
        raise


@app.on_event("shutdown")
async def on_shutdown():
    """Удаляет webhook при остановке."""
    logger.info("Удаляю webhook...")
    try:
        await bot.delete_webhook()
    except Exception as exc:
        logger.warning(f"Ошибка при удалении webhook: {exc}")
    await bot.session.close()


@app.post(config.WEBHOOK_PATH)
async def webhook(request: Request) -> JSONResponse:
    """Принимает обновления от Telegram через webhook."""
    from aiogram.types import Update

    # Проверка secret token (защита от поддельных запросов)
    received_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if config.WEBHOOK_SECRET_TOKEN and received_token != config.WEBHOOK_SECRET_TOKEN:
        logger.warning(f"Webhook rejected: invalid secret token ({received_token})")
        return JSONResponse(status_code=403, content={"ok": False, "error": "Forbidden"})

    try:
        update_data = await request.json()
        update = Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_update(bot, update)
        return JSONResponse(content={"ok": True})
    except Exception as exc:
        logger.exception(f"Ошибка обработки webhook: {exc}")
        return JSONResponse(status_code=200, content={"ok": False, "error": str(exc)})


@app.get("/health")
async def health() -> JSONResponse:
    """Health-check эндпоинт."""
    return JSONResponse(content={"status": "ok", "bot": "HeroSMS"})


@app.get("/")
async def root() -> JSONResponse:
    """Корневой эндпоинт."""
    return JSONResponse(content={
        "name": "HeroSMS Bot",
        "version": "1.0.0",
        "status": "running",
    })


# ─── Polling-режим для локальной разработки ───────────────────────────

async def start_polling():
    """Запускает бота в режиме polling (для локальной разработки)."""
    logger.info("Запуск в режиме polling...")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as exc:
        logger.warning(f"Ошибка при удалении webhook: {exc}")

    logger.info("Бот запущен! Нажмите Ctrl+C для остановки.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    # Проверяем аргументы командной строки
    if "--polling" in sys.argv or "-p" in sys.argv:
        # Polling режим
        asyncio.run(start_polling())
    else:
        # Webhook режим (по умолчанию)
        import uvicorn

        logger.info(f"Запуск webhook сервера на {config.WEBAPP_HOST}:{config.WEBAPP_PORT}")
        uvicorn.run(
            "main:app",
            host=config.WEBAPP_HOST,
            port=config.WEBAPP_PORT,
            reload=True if "--reload" in sys.argv else False,
            log_level="info",
        )
