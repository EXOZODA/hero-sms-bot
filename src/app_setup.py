"""
Настройка FastAPI приложения и Telegram бота.
Вынесено в отдельный файл, чтобы избежать двойной загрузки модуля.
"""

import logging
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.bot.handlers import router as bot_router
from src.bot.middlewares import (
    ErrorHandlingMiddleware,
    RateLimitMiddleware,
    UserMiddleware,
)
from src.config import Config

logger = logging.getLogger(__name__)

config = Config()

# ─── Создаём бота ──────────────────────────────────────────────────────

bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)


# ─── Создаём диспетчер ─────────────────────────────────────────────────

def create_dispatcher() -> Dispatcher:
    """Создаёт и настраивает Dispatcher."""
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

    return dp


dp = create_dispatcher()


# ─── Lifespan ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управляет жизненным циклом приложения."""
    # Startup
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

    yield  # Приложение работает

    # Shutdown
    logger.info("Удаляю webhook...")
    try:
        await bot.delete_webhook()
    except Exception as exc:
        logger.warning(f"Ошибка при удалении webhook: {exc}")
    await bot.session.close()


# ─── FastAPI приложение ────────────────────────────────────────────────

app = FastAPI(title="HeroSMS Bot", lifespan=lifespan)


@app.post(config.WEBHOOK_PATH)
async def webhook(request: Request) -> JSONResponse:
    """Принимает обновления от Telegram через webhook."""
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
