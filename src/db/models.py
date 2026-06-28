"""
Модели данных для БД.
Используются Pydantic модели для представления записей таблиц.

Таблицы:
  - users: пользователи
  - rents: аренды/активации
  - sms_messages: полученные SMS
  - transactions: транзакции
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """Пользователь бота."""
    id: Optional[int] = None
    telegram_id: int = 0
    username: Optional[str] = None
    balance: float = 0.0
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class Rent:
    """Аренда или активация номера.

    Типы:
      - activation: 20-минутная активация
      - rent: полноценная аренда (от 4 часов)

    Статусы:
      - active: активна
      - waiting_sms: ожидание SMS
      - completed: завершена
      - cancelled: отменена
      - expired: истекла
    """
    id: Optional[int] = None
    user_id: int = 0
    phone: str = ""
    service: str = ""
    service_name: Optional[str] = None
    country: str = ""
    country_id: int = 0
    rent_type: str = "activation"  # activation | rent
    duration_hours: Optional[int] = None
    status: str = "active"
    hero_activation_id: Optional[int] = None
    hero_rent_id: Optional[int] = None
    price: float = 0.0
    created_at: datetime = None
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class SMSMessage:
    """SMS-сообщение, полученное на арендованный номер."""
    id: Optional[int] = None
    rent_id: int = 0
    text: str = ""
    code: Optional[str] = None
    received_at: datetime = None

    def __post_init__(self):
        if self.received_at is None:
            self.received_at = datetime.utcnow()


@dataclass
class Transaction:
    """Транзакция пользователя (пополнение/списание)."""
    id: Optional[int] = None
    user_id: int = 0
    amount: float = 0.0
    type: str = "spend"  # deposit | spend | refund
    description: str = ""
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
