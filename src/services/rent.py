"""
Бизнес-логика аренды номеров.

Связывает Telegram-бот (handlers) с HeroSMS API и БД (repository).
Все функции асинхронные.

Поток работы:
  1. Пользователь выбирает параметры (сервис, страна, тип, длительность)
  2. Сервис проверяет баланс
  3. Вызывает API HeroSMS (getNumber / getRentNumber)
  4. Сохраняет аренду в БД
  5. Списывает средства
  6. Возвращает пользователю номер
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Sequence

import aiosqlite
import httpx

from src.api.hero_client import (
    HeroSMSClient,
    InsufficientBalanceError,
    NoNumbersError,
    ApiError,
)
from src.config import Config
from src.db.models import Rent, SMSMessage, Transaction, User
from src.db.repository import (
    add_user_balance,
    create_rent as db_create_rent,
    create_transaction,
    deduct_user_balance,
    get_active_rents_by_user_id,
    get_all_active_rents,
    get_expired_rents,
    get_or_create_user,
    get_rent_by_id,
    get_sms_by_rent_id,
    get_total_spent,
    get_user_by_telegram_id,
    save_sms,
    update_rent_status,
)

logger = logging.getLogger(__name__)

# Регулярка для извлечения кода из SMS (4-8 цифр)
CODE_REGEX = re.compile(r"(\d{4,8})")


class RentService:
    """Сервис аренды номеров."""

    def __init__(self, config: Config, db: aiosqlite.Connection):
        self.config = config
        self.db = db
        self.api = HeroSMSClient(api_key=config.HERO_SMS_API_KEY)

    async def close(self):
        """Закрыть соединения."""
        await self.api.close()

    # ─── Пользователи ────────────────────────────────────────────────

    async def get_or_create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
    ) -> User:
        """Получить или создать пользователя."""
        return await get_or_create_user(self.db, telegram_id, username)

    async def get_user_balance(self, telegram_id: int) -> float:
        """Получить баланс пользователя."""
        user = await get_user_by_telegram_id(self.db, telegram_id)
        return user.balance if user else 0.0

    async def get_total_spent(self, telegram_id: int) -> float:
        """Получить сумму трат пользователя."""
        return await get_total_spent(self.db, telegram_id)

    async def topup_balance(
        self,
        telegram_id: int,
        amount: float,
        description: str = "Пополнение баланса",
    ) -> float:
        """Пополнить баланс пользователя."""
        new_balance = await add_user_balance(self.db, telegram_id, amount)
        user = await get_user_by_telegram_id(self.db, telegram_id)
        if user:
            await create_transaction(self.db, Transaction(
                user_id=user.id,
                amount=amount,
                type="deposit",
                description=description,
            ))
        return new_balance

    # ─── Аренда ──────────────────────────────────────────────────────

    async def start_activation(
        self,
        telegram_id: int,
        service: str,
        country: int,
        service_name: Optional[str] = None,
        country_name: Optional[str] = None,
        operator: Optional[str] = None,
    ) -> Rent:
        """Начать активацию (20 мин).

        Args:
            telegram_id: ID пользователя в Telegram
            service: Код сервиса (tg, wa, ig, ...)
            country: ID страны
            service_name: Название сервиса
            country_name: Название страны
            operator: Предпочитаемый оператор

        Returns:
            Rent: объект аренды

        Raises:
            InsufficientBalanceError: не хватает средств
            NoNumbersError: нет номеров
            ApiError: ошибка API
        """
        # Получаем пользователя
        user = await get_or_create_user(self.db, telegram_id)

        # Получаем цену
        price = await self._get_activation_price(service, country)

        # Проверяем баланс
        if user.balance < price:
            raise InsufficientBalanceError(
                f"Недостаточно средств. Нужно: ${price:.2f}, "
                f"на балансе: ${user.balance:.2f}"
            )

        # Запрашиваем номер через API
        try:
            activation_id, phone = await self.api.get_number(
                service=service,
                country=country,
                max_price=price,
                operator=operator,
            )
        except NoNumbersError:
            raise
        except ApiError as e:
            logger.error(f"API error during activation: {e}")
            raise

        # Создаём запись аренды
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=20)

        rent = Rent(
            user_id=user.id,
            phone=phone,
            service=service,
            service_name=service_name,
            country=country_name or str(country),
            country_id=country,
            rent_type="activation",
            duration_hours=None,
            status="active",
            hero_activation_id=activation_id,
            price=price,
            created_at=now,
            expires_at=expires_at,
        )

        rent = await db_create_rent(self.db, rent)

        # Списываем средства
        await deduct_user_balance(self.db, telegram_id, price)
        await create_transaction(self.db, Transaction(
            user_id=user.id,
            amount=-price,
            type="spend",
            description=f"Активация {service} ({country_name or country}) — {phone}",
        ))

        logger.info(
            f"Activation started: user={telegram_id}, "
            f"service={service}, country={country}, "
            f"phone={phone}, price=${price:.2f}"
        )

        return rent

    async def start_rent(
        self,
        telegram_id: int,
        service: str,
        country: int,
        hours: int,
        service_name: Optional[str] = None,
        country_name: Optional[str] = None,
        operator: Optional[str] = None,
    ) -> Rent:
        """Начать аренду номера.

        Args:
            telegram_id: ID пользователя в Telegram
            service: Код сервиса
            country: ID страны
            hours: Количество часов аренды
            service_name: Название сервиса
            country_name: Название страны
            operator: Предпочитаемый оператор

        Returns:
            Rent: объект аренды
        """
        user = await get_or_create_user(self.db, telegram_id)

        # Рассчитываем цену
        price = await self._get_rent_price(service, country, hours)

        # Проверяем баланс
        if user.balance < price:
            raise InsufficientBalanceError(
                f"Недостаточно средств. Нужно: ${price:.2f}, "
                f"на балансе: ${user.balance:.2f}"
            )

        # Запрашиваем аренду через API
        try:
            rent_id, phone = await self.api.get_rent_number(
                service=service,
                country=country,
                hours=hours,
                operator=operator,
            )
        except NoNumbersError:
            raise
        except ApiError as e:
            logger.error(f"API error during rent: {e}")
            raise

        # Создаём запись
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=hours)

        rent = Rent(
            user_id=user.id,
            phone=phone,
            service=service,
            service_name=service_name,
            country=country_name or str(country),
            country_id=country,
            rent_type="rent",
            duration_hours=hours,
            status="active",
            hero_activation_id=None,
            hero_rent_id=rent_id,
            price=price,
            created_at=now,
            expires_at=expires_at,
        )

        rent = await db_create_rent(self.db, rent)

        # Списываем средства
        await deduct_user_balance(self.db, telegram_id, price)
        await create_transaction(self.db, Transaction(
            user_id=user.id,
            amount=-price,
            type="spend",
            description=f"Аренда {service} ({country_name or country}) — {phone} на {hours}ч",
        ))

        logger.info(
            f"Rent started: user={telegram_id}, "
            f"service={service}, country={country}, "
            f"hours={hours}, phone={phone}, price=${price:.2f}"
        )

        return rent

    # ─── Получение SMS ───────────────────────────────────────────────

    async def check_sms(self, rent_id: int) -> Sequence[SMSMessage]:
        """Проверить новые SMS для аренды.

        Сначала проверяет в локальной БД, затем запрашивает с API.

        Args:
            rent_id: ID аренды

        Returns:
            list[SMSMessage]: список SMS
        """
        # Сначала проверяем локально
        local_sms = await get_sms_by_rent_id(self.db, rent_id)
        if local_sms:
            return local_sms

        # Если нет локально — запрашиваем с API
        rent = await get_rent_by_id(self.db, rent_id)
        if rent is None:
            return []

        activation_id = rent.hero_activation_id or rent.hero_rent_id
        if activation_id is None:
            return []

        try:
            api_sms_list = await self.api.get_all_sms(activation_id)

            saved_sms = []
            for sms_data in api_sms_list:
                text = sms_data.get("text", str(sms_data))
                code = self._extract_code(text)

                sms = SMSMessage(
                    rent_id=rent_id,
                    text=text,
                    code=code,
                )
                sms = await save_sms(self.db, sms)
                saved_sms.append(sms)

            # Обновляем статус, если получили код
            if saved_sms and rent.status == "active":
                await update_rent_status(self.db, rent_id, "waiting_sms")

            return saved_sms or local_sms

        except ApiError:
            logger.warning(f"Failed to fetch SMS for rent {rent_id}, returning local")
            return local_sms

    # ─── Управление арендой ──────────────────────────────────────────

    async def cancel_rent(self, rent_id: int, telegram_id: int) -> bool:
        """Отменить аренду.

        Args:
            rent_id: ID аренды
            telegram_id: ID пользователя (для проверки владельца)

        Returns:
            bool: успешно ли отменено
        """
        rent = await get_rent_by_id(self.db, rent_id)
        if rent is None:
            return False

        user = await get_user_by_telegram_id(self.db, telegram_id)
        if user is None or rent.user_id != user.id:
            return False

        # Отменяем в API
        try:
            if rent.hero_activation_id:
                await self.api.set_status(rent.hero_activation_id, 8)
            elif rent.hero_rent_id:
                await self.api.set_rent_status(rent.hero_rent_id, 2)
        except ApiError as e:
            logger.warning(f"API cancel failed for rent {rent_id}: {e}")
            # Продолжаем, даже если API отказ

        # Обновляем статус в БД
        await update_rent_status(self.db, rent_id, "cancelled")

        # Возвращаем средства (если активация — возврат полный, аренда — частичный)
        if rent.rent_type == "activation":
            await add_user_balance(self.db, telegram_id, rent.price)
            await create_transaction(self.db, Transaction(
                user_id=user.id,
                amount=rent.price,
                type="refund",
                description=f"Возврат за отмену активации #{rent_id}",
            ))

        logger.info(f"Rent cancelled: rent_id={rent_id}, user={telegram_id}")
        return True

    async def extend_rent(
        self,
        rent_id: int,
        telegram_id: int,
        additional_hours: int,
    ) -> Optional[datetime]:
        """Продлить аренду.

        Args:
            rent_id: ID аренды
            telegram_id: ID пользователя
            additional_hours: На сколько часов продлить

        Returns:
            datetime: новая дата истечения (None при ошибке)
        """
        from src.db.repository import extend_rent as db_extend_rent
        return await db_extend_rent(self.db, rent_id, additional_hours)

    # ─── Пользовательские аренды ─────────────────────────────────────

    async def get_active_rents(self, telegram_id: int) -> Sequence[Rent]:
        """Получить активные аренды пользователя."""
        user = await get_user_by_telegram_id(self.db, telegram_id)
        if user is None:
            return []
        return await get_active_rents_by_user_id(self.db, user.id)

    async def get_rent_detail(self, rent_id: int) -> Optional[Rent]:
        """Получить детали аренды."""
        return await get_rent_by_id(self.db, rent_id)

    # ─── Фоновые задачи ──────────────────────────────────────────────

    async def auto_expire_rents(self):
        """Автоматически завершить просроченные аренды."""
        expired = await get_expired_rents(self.db)
        for rent in expired:
            await update_rent_status(self.db, rent.id, "expired")
            logger.info(f"Rent expired automatically: rent_id={rent.id}")

    # ─── Цены ─────────────────────────────────────────────────────────

    async def _get_activation_price(
        self,
        service: str,
        country: int,
    ) -> float:
        """Получить цену активации из API."""
        try:
            prices = await self.api.get_prices(service, country)
            # Парсим цены (формат зависит от API)
            if isinstance(prices, dict):
                # Может быть вложенная структура
                country_str = str(country)
                if country_str in prices:
                    data = prices[country_str]
                    if isinstance(data, dict):
                        return float(data.get("cost", data.get("price", 0.5)))
                    return float(data) if data else 0.5
            return 0.5
        except (ApiError, ValueError, TypeError):
            logger.warning(f"Failed to get price for {service}/{country}, using default")
            return 0.5

    async def _get_rent_price(
        self,
        service: str,
        country: int,
        hours: int,
    ) -> float:
        """Рассчитать цену аренды."""
        try:
            prices = await self.api.get_prices(service, country)
            country_str = str(country)
            if isinstance(prices, dict) and country_str in prices:
                data = prices[country_str]
                if isinstance(data, dict):
                    price_per_hour = float(data.get("cost", data.get("price", 0.2)))
                else:
                    price_per_hour = float(data) if data else 0.2
            else:
                price_per_hour = 0.2

            return round(price_per_hour * hours, 2)
        except (ApiError, ValueError, TypeError):
            logger.warning(f"Failed to get rent price for {service}/{country}, using default")
            return round(0.2 * hours, 2)

    # ─── Утилиты ──────────────────────────────────────────────────────

    @staticmethod
    def _extract_code(text: str) -> Optional[str]:
        """Извлечь код подтверждения из текста SMS."""
        match = CODE_REGEX.search(text)
        return match.group(1) if match else None
