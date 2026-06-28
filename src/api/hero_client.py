"""
Асинхронный клиент для HeroSMS API.

Поддерживает два формата:
  - SMS-Activate совместимый (GET с параметрами)
  - HeroSMS REST API v1

Base URL: https://hero-sms.com/stubs/handler_api.php (SMS-Activate совместимый)
"""

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class HeroSMSError(Exception):
    """Базовое исключение HeroSMS API."""
    pass


class InsufficientBalanceError(HeroSMSError):
    """Недостаточно средств на балансе."""
    pass


class NoNumbersError(HeroSMSError):
    """Нет доступных номеров."""
    pass


class BannedError(HeroSMSError):
    """Аккаунт заблокирован."""
    pass


class WrongMaxPriceError(HeroSMSError):
    """Некорректная максимальная цена."""
    pass


class BadActionError(HeroSMSError):
    """Некорректное действие."""
    pass


class ApiError(HeroSMSError):
    """Общая ошибка API."""
    pass


# Маппинг ошибок SMS-Activate протокола
ERROR_MAP = {
    "NO_BALANCE": InsufficientBalanceError,
    "NO_NUMBERS": NoNumbersError,
    "BANNED": BannedError,
    "WRONG_MAX_PRICE": WrongMaxPriceError,
    "WRONG_SERVICE": BadActionError,
    "WRONG_COUNTRY": BadActionError,
    "INCORRECT_STATUS": BadActionError,
    "BAD_ACTION": BadActionError,
    "ERROR": ApiError,
}


class HeroSMSClient:
    """Асинхронный клиент HeroSMS API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://hero-sms.com/stubs/handler_api.php",
        timeout: int = 30,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self._session: Optional[httpx.AsyncClient] = None

    async def _get_session(self) -> httpx.AsyncClient:
        """Получить или создать HTTP-сессию."""
        if self._session is None or self._session.is_closed:
            self._session = httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": "HeroSMSBot/1.0"},
            )
        return self._session

    async def _request(self, action: str, params: dict[str, Any] = None) -> str:
        """Отправить GET-запрос к SMS-Activate совместимому API.

        Args:
            action: Название действия (getBalance, getNumber, ...)
            params: Дополнительные параметры

        Returns:
            Сырой текстовый ответ от API

        Raises:
            HeroSMSError: при ошибке API
        """
        session = await self._get_session()
        request_params = {
            "api_key": self.api_key,
            "action": action,
        }
        if params:
            request_params.update(params)

        try:
            response = await session.get(self.base_url, params=request_params)
            response.raise_for_status()
            text = response.text.strip()
            logger.debug(f"API response [{action}]: {text[:200]}")

            # Проверка на ошибки
            if text.startswith("NO_"):
                error_class = ERROR_MAP.get(text.split("\n")[0], ApiError)
                raise error_class(f"API error: {text}")

            if text.startswith("BAD_"):
                raise BadActionError(f"API error: {text}")

            if text == "BANNED":
                raise BannedError("Account is banned")

            return text

        except httpx.TimeoutException:
            logger.error(f"API request timeout for action={action}")
            raise ApiError(f"Request timeout for action={action}")
        except httpx.HTTPStatusError as e:
            logger.error(f"API HTTP error for action={action}: {e}")
            raise ApiError(f"HTTP {e.response.status_code}: {e.response.text}")

    async def _request_json(self, action: str, params: dict[str, Any] = None) -> dict:
        """Отправить запрос и распарсить JSON-ответ."""
        text = await self._request(action, params)
        import json
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Некоторые методы возвращают текст, а не JSON
            return {"raw": text}

    async def close(self):
        """Закрыть HTTP-сессию."""
        if self._session and not self._session.is_closed:
            await self._session.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    # ─── API методы ──────────────────────────────────────────────────

    async def get_balance(self) -> float:
        """Получить текущий баланс аккаунта.

        Returns:
            float: баланс в USD

        Raises:
            InsufficientBalanceError: если баланс 0 (крайний случай)
        """
        text = await self._request("getBalance")
        # Формат ответа: ACCESS_BALANCE:12.34
        if text.startswith("ACCESS_BALANCE:"):
            return float(text.split(":", 1)[1])
        return 0.0

    async def get_countries(self) -> dict[int, dict]:
        """Получить список стран.

        Returns:
            dict: {country_id: {"name": str, "rus_name": str, ...}}
        """
        text = await self._request("getCountries")
        import json
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse countries response: {text[:100]}")
            return {}

    async def get_services_list(self) -> dict[str, Any]:
        """Получить список сервисов.

        Returns:
            dict: {service_code: service_name}
        """
        text = await self._request("getServicesList")
        import json
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse services list: {text[:100]}")
            return {}

    async def get_prices(
        self,
        service: str,
        country: Optional[int] = None,
    ) -> dict:
        """Получить цены для сервиса и страны.

        Args:
            service: Код сервиса (tg, wa, ig, ...)
            country: ID страны (опционально)

        Returns:
            dict с ценами
        """
        params = {"service": service}
        if country is not None:
            params["country"] = str(country)

        text = await self._request("getPrices", params)
        import json
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse prices: {text[:100]}")
            return {}

    async def get_number(
        self,
        service: str,
        country: int,
        max_price: Optional[float] = None,
        operator: Optional[str] = None,
    ) -> tuple[int, str]:
        """Получить номер для активации (20 мин).

        Args:
            service: Код сервиса (tg, wa, ig, ...)
            country: ID страны
            max_price: Максимальная цена
            operator: Предпочитаемый оператор

        Returns:
            tuple: (activation_id, phone_number)

        Raises:
            NoNumbersError: нет доступных номеров
            InsufficientBalanceError: не хватает средств
        """
        params = {
            "service": service,
            "country": str(country),
        }
        if max_price is not None:
            params["maxPrice"] = str(max_price)
        if operator:
            params["operator"] = operator

        text = await self._request("getNumber", params)
        # Формат: ACCESS_NUMBER:activation_id:phone_number
        if text.startswith("ACCESS_NUMBER:"):
            parts = text.split(":")
            if len(parts) >= 3:
                return int(parts[1]), parts[2]
            raise ApiError(f"Unexpected response format: {text}")

        # getNumberV2: {"status": "success", ...}
        raise ApiError(f"Unexpected response: {text}")

    async def get_number_v2(
        self,
        service: str,
        country: int,
        max_price: Optional[float] = None,
        operator: Optional[str] = None,
    ) -> dict:
        """Получить номер через getNumberV2 (более детальный ответ).

        Returns:
            dict: {"activation_id": int, "phone": str, ...}
        """
        params = {
            "service": service,
            "country": str(country),
        }
        if max_price is not None:
            params["maxPrice"] = str(max_price)
        if operator:
            params["operator"] = operator

        text = await self._request("getNumberV2", params)
        import json
        try:
            data = json.loads(text)
            if data.get("status") == "success":
                return data
            raise ApiError(f"API error: {data.get('message', text)}")
        except json.JSONDecodeError:
            raise ApiError(f"Unexpected response: {text}")

    async def get_rent_number(
        self,
        service: str,
        country: int,
        hours: int,
        operator: Optional[str] = None,
    ) -> tuple[int, str]:
        """Арендовать номер.

        Args:
            service: Код сервиса
            country: ID страны
            hours: Количество часов аренды
            operator: Предпочитаемый оператор

        Returns:
            tuple: (rent_id, phone_number)
        """
        params = {
            "service": service,
            "country": str(country),
            "hours": str(hours),
        }
        if operator:
            params["operator"] = operator

        text = await self._request("getRentNumber", params)
        # Формат: ACCESS_NUMBER:rent_id:phone_number
        if text.startswith("ACCESS_NUMBER:"):
            parts = text.split(":")
            if len(parts) >= 3:
                return int(parts[1]), parts[2]
            raise ApiError(f"Unexpected response format: {text}")
        raise ApiError(f"Unexpected response: {text}")

    async def get_status(self, activation_id: int) -> dict:
        """Получить статус активации.

        Returns:
            dict: {"status": str, "code": str|None, ...}
        """
        text = await self._request("getStatus", {"id": str(activation_id)})
        # Формат: STATUS_WAIT_CODE, STATUS_OK:code, STATUS_CANCEL, ...
        if text.startswith("STATUS_"):
            parts = text.split(":", 1)
            result = {"status": parts[0]}
            if len(parts) > 1:
                result["code"] = parts[1]
            return result
        return {"status": text}

    async def get_status_v2(self, activation_id: int) -> dict:
        """Получить статус активации (V2, более детально)."""
        text = await self._request("getStatusV2", {"id": str(activation_id)})
        import json
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text}

    async def set_status(
        self,
        activation_id: int,
        status: int,
    ) -> bool:
        """Установить статус активации.

        Статусы:
          1 — готов к приёму SMS (markReady)
          3 — запросить повторную отправку
          6 — завершить активацию
          8 — отменить активацию

        Returns:
            bool: успешно ли выполнено
        """
        text = await self._request("setStatus", {
            "id": str(activation_id),
            "status": str(status),
        })
        return "ACCESS" in text or "SUCCESS" in text

    async def get_rent_status(self, rent_id: int) -> dict:
        """Получить статус аренды.

        Returns:
            dict: с информацией о статусе аренды
        """
        text = await self._request("getRentStatus", {"id": str(rent_id)})
        import json
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text}

    async def set_rent_status(
        self,
        rent_id: int,
        status: int,
    ) -> bool:
        """Установить статус аренды.

        Статусы:
          2 — отменить аренду с возвратом
          3 — отменить аренду без возврата
        """
        text = await self._request("setRentStatus", {
            "id": str(rent_id),
            "status": str(status),
        })
        return "ACCESS" in text or "SUCCESS" in text

    async def get_all_sms(self, activation_id: int) -> list[dict]:
        """Получить все SMS для активации.

        Returns:
            list[dict]: список SMS с текстом и временем
        """
        text = await self._request("getAllSms", {"id": str(activation_id)})
        import json
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse SMS list: {text[:100]}")
            return []

    async def get_rent_services_and_countries(self) -> dict:
        """Получить список сервисов и стран, поддерживающих аренду."""
        text = await self._request("getRentServicesAndCountries")
        import json
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse rent services: {text[:100]}")
            return {}

    async def service_count_rent(self, service: str) -> dict:
        """Получить количество доступных номеров для аренды."""
        text = await self._request("serviceCountRent", {"service": service})
        import json
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text}
