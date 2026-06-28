"""
Middleware для передачи RentService в обработчики.
"""

import logging
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from src.services.rent import RentService

logger = logging.getLogger(__name__)


class RentServiceMiddleware(BaseMiddleware):
    """
    Middleware, который создаёт RentService при первом запросе
    и добавляет его в data['rent_service'].

    RentService инициализируется лениво (при первом обращении),
    чтобы не блокировать старт приложения.
    """

    def __init__(self, config):
        super().__init__()
        self.config = config
        self._rent_service: Optional[RentService] = None
        self._initialized = False

    async def _ensure_initialized(self):
        """Создаёт БД и RentService при первом вызове."""
        if self._initialized:
            return

        from pathlib import Path
        import aiosqlite
        from src.db.repository import create_tables

        db_path = Path(__file__).parent.parent.parent / "data.db"
        logger.info(f"Инициализация БД: {db_path}")

        # Создаём таблицы
        await create_tables(str(db_path))

        # Открываем постоянное соединение с БД
        db = await aiosqlite.connect(str(db_path))
        db.row_factory = aiosqlite.Row

        # Создаём RentService
        self._rent_service = RentService(self.config, db)
        self._initialized = True
        logger.info("RentService инициализирован")

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        try:
            await self._ensure_initialized()
        except Exception as exc:
            logger.exception(f"Не удалось инициализировать RentService: {exc}")
            # Пропускаем запрос — сервис недоступен
            if isinstance(event, Message):
                await event.answer("❌ Сервис временно недоступен. Попробуйте позже.")
            elif isinstance(event, CallbackQuery):
                try:
                    await event.answer("❌ Сервис недоступен", show_alert=True)
                except Exception:
                    pass
            return None

        data["rent_service"] = self._rent_service
        return await handler(event, data)
