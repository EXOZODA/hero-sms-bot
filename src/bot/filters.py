from typing import Union

from aiogram.enums import ChatType
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery


class IsPrivateChat(BaseFilter):
    """Фильтр: только личные сообщения с ботом."""

    async def __call__(self, event: Union[Message, CallbackQuery]) -> bool:
        if isinstance(event, Message):
            return event.chat.type == ChatType.PRIVATE
        if isinstance(event, CallbackQuery):
            return event.message.chat.type == ChatType.PRIVATE
        return False


class RentOwnerFilter(BaseFilter):
    """
    Фильтр: проверяет, что аренда принадлежит пользователю.
    Используется с rent_id из callback_data.
    """

    def __init__(self, rent_id_index: int = 1):
        """
        Args:
            rent_id_index: индекс rent_id в callback_data, разделённой двоеточием.
        """
        self.rent_id_index = rent_id_index

    async def __call__(self, query: CallbackQuery) -> bool:
        """
        Проверяет принадлежность аренды пользователю.
        В реальном проекте делает запрос в БД.
        """
        try:
            parts = query.data.split(":")
            if len(parts) > self.rent_id_index:
                rent_id = int(parts[self.rent_id_index])
                # TODO: проверить в БД, что rent.user_id == query.from_user.id
                _ = rent_id  # заглушка
                return True
        except (ValueError, IndexError):
            return False
        return True
