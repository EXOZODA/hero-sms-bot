"""
Middleware для aiogram 3.x:
- UserMiddleware — подгрузка/создание пользователя
- RateLimitMiddleware — ограничение частоты запросов
- ErrorHandlingMiddleware — логирование ошибок
"""

import time
import logging
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

logger = logging.getLogger(__name__)


class UserMiddleware(BaseMiddleware):
    """
    Загружает или создаёт пользователя при каждом сообщении.
    В реальном проекте делает запрос в БД.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id: Optional[int] = None
        username: Optional[str] = None
        full_name: Optional[str] = None

        if isinstance(event, Message):
            user = event.from_user
            if user:
                user_id = user.id
                username = user.username or f"user_{user.id}"
                full_name = user.full_name
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            if user:
                user_id = user.id
                username = user.username or f"user_{user.id}"
                full_name = user.full_name

        if user_id:
            # TODO: запрос в БД — get_or_create_user(user_id, username, full_name)
            # Пока просто прокидываем данные
            data["user_id"] = user_id
            data["username"] = username
            data["full_name"] = full_name

            # Заглушка: "загруженный" пользователь
            data["user"] = {
                "id": user_id,
                "username": username,
                "full_name": full_name,
                "balance": 100.0,
                "total_spent": 25.0,
                "is_active": True,
            }

        return await handler(event, data)


class RateLimitMiddleware(BaseMiddleware):
    """
    Ограничение запросов: не чаще 1 запроса в секунду.
    Хранит временные метки последних запросов в памяти.
    """

    def __init__(self, rate_limit: float = 1.0):
        super().__init__()
        self.rate_limit = rate_limit
        self.last_request: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id: Optional[int] = None

        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_id = event.from_user.id

        if user_id:
            now = time.time()
            last = self.last_request.get(user_id, 0.0)

            if now - last < self.rate_limit:
                # Превышен лимит — игнорируем запрос
                logger.warning(
                    f"Rate limit exceeded for user {user_id}: "
                    f"{now - last:.2f}s < {self.rate_limit}s"
                )
                # Для кастомных клавиатур можно ответить на callback
                if isinstance(event, CallbackQuery):
                    try:
                        await event.answer(
                            "⏳ Пожалуйста, не так быстро!",
                            show_alert=False,
                        )
                    except Exception:
                        pass
                return None

            self.last_request[user_id] = now

        return await handler(event, data)


class ErrorHandlingMiddleware(BaseMiddleware):
    """
    Логирует ошибки и уведомляет пользователя.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as exc:
            logger.exception(
                f"Unhandled error in handler for {type(event).__name__}: {exc}"
            )
            # Пытаемся уведомить пользователя
            try:
                from src.bot.texts import Texts
                bot = data.get("bot")
                if bot:
                    if isinstance(event, Message):
                        await event.answer(Texts.error_message())
                    elif isinstance(event, CallbackQuery) and event.message:
                        await event.message.answer(Texts.error_message())
            except Exception:
                pass
            return None
