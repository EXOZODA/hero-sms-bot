"""
Обработчики команд и callback'ов Telegram бота.
Содержит заглушки для backend-сервисов.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from src.bot.filters import IsPrivateChat
from src.bot.keyboards import (
    COUNTRIES,
    SERVICES,
    ITEMS_PER_PAGE,
    back_kb,
    back_main_kb,
    balance_kb,
    cancel_kb,
    confirm_kb,
    country_selection_kb,
    duration_selection_kb,
    extend_duration_kb,
    main_menu_kb,
    my_rents_kb,
    rent_control_kb,
    rent_type_kb,
    service_selection_kb,
    topup_kb,
)
from src.bot.states import RentStates, TopUpStates
from src.bot.texts import Texts

logger = logging.getLogger(__name__)

router = Router()

# ─── Заглушки для backend-сервисов ────────────────────────────────────
# В реальном проекте эти функции будут импортироваться из:
#   from src.services.rent import start_rent, start_activation, check_sms
#   from src.db.repository import get_user, get_active_rents
#   from src.api.hero_client import get_balance

_rental_counter: int = 0
_active_rents: dict[int, dict] = {}


def _generate_phone() -> str:
    """Генерирует тестовый номер телефона."""
    import random
    codes = ["+1202555", "+447000", "+7910", "+38050", "+48500"]
    prefix = random.choice(codes)
    suffix = "".join(str(random.randint(0, 9)) for _ in range(4))
    return f"{prefix}{suffix}"


async def _stub_create_rent(
    user_id: int,
    service_code: str,
    service_name: str,
    country_id: int,
    country_name: str,
    country_flag: str,
    rent_type: str,
    duration: Optional[int],
    price: float,
) -> dict:
    """Заглушка: создаёт аренду и возвращает её данные."""
    global _rental_counter
    _rental_counter += 1

    now = datetime.utcnow()
    if rent_type == "activation":
        expires = now + timedelta(minutes=20)
    elif duration:
        expires = now + timedelta(hours=duration)
    else:
        expires = now + timedelta(hours=4)

    rent = {
        "id": _rental_counter,
        "user_id": user_id,
        "phone": _generate_phone(),
        "service_code": service_code,
        "service_name": service_name,
        "country_id": country_id,
        "country_name": country_name,
        "country_flag": country_flag,
        "rent_type": rent_type,
        "duration": duration,
        "price": price,
        "sms": [],
        "created_at": now.isoformat(),
        "expires_at": expires.isoformat(),
        "is_active": True,
    }
    _active_rents[rent["id"]] = rent
    return rent


async def _stub_get_rent(rent_id: int) -> Optional[dict]:
    """Заглушка: возвращает аренду по ID."""
    return _active_rents.get(rent_id)


async def _stub_cancel_rent(rent_id: int, user_id: int) -> bool:
    """Заглушка: отменяет аренду."""
    rent = _active_rents.get(rent_id)
    if rent and rent["user_id"] == user_id and rent["is_active"]:
        rent["is_active"] = False
        return True
    return False


async def _stub_extend_rent(rent_id: int, user_id: int, extra_hours: int) -> Optional[str]:
    """Заглушка: продлевает аренду на N часов."""
    rent = _active_rents.get(rent_id)
    if not rent or rent["user_id"] != user_id or not rent["is_active"]:
        return None

    old_expires = datetime.fromisoformat(rent["expires_at"])
    new_expires = old_expires + timedelta(hours=extra_hours)
    rent["expires_at"] = new_expires.isoformat()
    return new_expires.strftime("%Y-%m-%d %H:%M UTC")


async def _stub_check_sms(rent_id: int) -> list[str]:
    """Заглушка: проверяет SMS."""
    import random
    rent = _active_rents.get(rent_id)
    if not rent:
        return []

    # Симулируем получение SMS (при первом запросе)
    if not rent["sms"]:
        code = "".join(str(random.randint(0, 9)) for _ in range(6))
        rent["sms"].append(code)

    return rent["sms"]


async def _stub_get_active_rents(user_id: int) -> list[dict]:
    """Заглушка: возвращает активные аренды пользователя."""
    return [
        r for r in _active_rents.values()
        if r["user_id"] == user_id and r["is_active"]
    ]


async def _stub_get_user_balance(user_id: int) -> float:
    """Заглушка: возвращает баланс пользователя."""
    return 100.0


async def _stub_get_user_total_spent(user_id: int) -> float:
    """Заглушка: возвращает потраченную сумму."""
    return 25.0


def _calculate_price(
    service_code: str,
    country_id: int,
    rent_type: str,
    duration: Optional[int] = None,
) -> float:
    """Рассчитывает цену на основе тарифов."""
    base_activation = 0.50
    base_per_hour = 0.20

    # Поиск страны
    country = next((c for c in COUNTRIES if c["id"] == country_id), None)
    if country:
        base_activation = country["price_activation"]
        base_per_hour = country["price_per_hour"]

    if rent_type == "activation":
        return base_activation
    elif rent_type == "rent" and duration:
        return round(base_per_hour * duration, 2)

    return base_activation


def _get_country_by_id(country_id: int) -> Optional[dict]:
    return next((c for c in COUNTRIES if c["id"] == country_id), None)


def _get_service_by_code(code: str) -> Optional[dict]:
    return next((s for s in SERVICES if s["code"] == code), None)


def _format_time_left(expires_at: str) -> str:
    """Форматирует оставшееся время."""
    try:
        expires = datetime.fromisoformat(expires_at)
        now = datetime.utcnow()
        delta = expires - now

        if delta.total_seconds() <= 0:
            return "⏳ Истекло"

        total_hours = int(delta.total_seconds() // 3600)
        minutes = int((delta.total_seconds() % 3600) // 60)

        if total_hours >= 24:
            days = total_hours // 24
            hours = total_hours % 24
            return f"{days} д {hours} ч"
        elif total_hours > 0:
            return f"{total_hours} ч {minutes} мин"
        else:
            return f"{minutes} мин"
    except (ValueError, TypeError):
        return "⏳ Неизвестно"


# ─── Вспомогательная функция для ответа ──────────────────────────────

async def _answer_or_edit(
    event: Message | CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup,
    parse_mode: str = "HTML",
) -> Message | None:
    """
    Если event — Message, отправляет новое сообщение.
    Если event — CallbackQuery, редактирует существующее.
    """
    if isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(
                text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )
        except Exception:
            # Если не удалось отредактировать (удалено, слишком старое)
            await event.message.delete()
            return await event.message.answer(
                text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )
        return None
    else:
        return await event.answer(
            text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
        )


async def _show_main_menu(
    event: Message | CallbackQuery,
    username: str,
    balance: float,
    active_count: int,
    state: FSMContext,
):
    """Показывает главное меню и сбрасывает FSM."""
    await state.clear()
    text = Texts.main_menu(username, balance, active_count)
    await _answer_or_edit(event, text, main_menu_kb())


# ─── Команды ───────────────────────────────────────────────────────────

@router.message(Command("start"), IsPrivateChat())
async def cmd_start(message: Message, state: FSMContext, **kwargs):
    """Обработчик команды /start."""
    await state.clear()

    user_id = kwargs.get("user_id", message.from_user.id)
    username = kwargs.get("username", message.from_user.username or f"user_{user_id}")

    # Показываем приветствие для нового пользователя
    text = Texts.welcome_new()
    await message.answer(text, reply_markup=main_menu_kb())


@router.message(Command("help"), IsPrivateChat())
async def cmd_help(message: Message, **kwargs):
    """Обработчик команды /help."""
    text = Texts.help_text()
    await message.answer(text, reply_markup=back_main_kb())


# ─── Главное меню ──────────────────────────────────────────────────────

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(query: CallbackQuery, state: FSMContext, **kwargs):
    """Возвращает в главное меню."""
    user_id = kwargs.get("user_id", query.from_user.id)
    username = kwargs.get("username", query.from_user.username or f"user_{user_id}")

    active_rents = await _stub_get_active_rents(user_id)
    balance = await _stub_get_user_balance(user_id)

    await _show_main_menu(query, username, balance, len(active_rents), state)
    await query.answer()


# ─── Помощь ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "help")
async def cb_help(query: CallbackQuery, **kwargs):
    """Показывает справку."""
    text = Texts.help_text()
    await _answer_or_edit(query, text, back_main_kb())
    await query.answer()


# ─── Начало аренды — выбор сервиса ─────────────────────────────────────

@router.callback_query(F.data == "rent")
async def cb_rent_start(query: CallbackQuery, state: FSMContext, **kwargs):
    """Начинает процесс аренды: показывает список сервисов."""
    await state.set_state(RentStates.choosing_service)
    await state.update_data(service_page=0)

    text = Texts.select_service()
    await _answer_or_edit(query, text, service_selection_kb())
    await query.answer()


@router.callback_query(F.data == "other_service")
async def cb_other_service(query: CallbackQuery, **kwargs):
    """Показывает информацию о других сервисах."""
    await query.answer("🔍 Введите название сервиса вручную", show_alert=True)
    text = Texts.other_service()
    await _answer_or_edit(query, text, back_kb())


# ─── Выбор сервиса ─────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("service:"), StateFilter(RentStates.choosing_service))
async def cb_service_selected(query: CallbackQuery, state: FSMContext, **kwargs):
    """Обрабатывает выбор сервиса."""
    code = query.data.split(":")[1]
    service = _get_service_by_code(code)

    if not service:
        await query.answer("🔧 Сервис не найден", show_alert=True)
        return

    await state.update_data(
        service_code=code,
        service_name=service["name"],
        country_page=0,
    )
    await state.set_state(RentStates.choosing_country)

    text = Texts.select_country(service["name"])
    await _answer_or_edit(query, text, country_selection_kb(page=0))
    await query.answer()


# ─── Выбор страны ──────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("country:"), StateFilter(RentStates.choosing_country))
async def cb_country_selected(query: CallbackQuery, state: FSMContext, **kwargs):
    """Обрабатывает выбор страны."""
    try:
        country_id = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        await query.answer("❌ Некорректный выбор", show_alert=True)
        return

    country = _get_country_by_id(country_id)
    if not country:
        await query.answer("🌍 Страна не найдена", show_alert=True)
        return

    data = await state.get_data()
    service_name = data.get("service_name", "Сервис")

    await state.update_data(
        country_id=country_id,
        country_name=country["name"],
        country_flag=country["flag"],
    )
    await state.set_state(RentStates.choosing_rent_type)

    text = Texts.select_rent_type(service_name, country["flag"], country["name"])
    await _answer_or_edit(query, text, rent_type_kb())
    await query.answer()


@router.callback_query(F.data.startswith("country_page:"), StateFilter(RentStates.choosing_country))
async def cb_country_page(query: CallbackQuery, state: FSMContext, **kwargs):
    """Пагинация списка стран."""
    try:
        page = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        await query.answer()
        return

    data = await state.get_data()
    service_name = data.get("service_name", "Сервис")

    await state.update_data(country_page=page)

    text = Texts.select_country(service_name)
    await _answer_or_edit(query, text, country_selection_kb(page=page))
    await query.answer()


# ─── Выбор типа аренды ─────────────────────────────────────────────────

@router.callback_query(F.data.startswith("rent_type:"), StateFilter(RentStates.choosing_rent_type))
async def cb_rent_type_selected(query: CallbackQuery, state: FSMContext, **kwargs):
    """Обрабатывает выбор типа аренды (активация / аренда)."""
    rent_type = query.data.split(":")[1]

    data = await state.get_data()
    service_code = data.get("service_code", "tg")
    country_id = data.get("country_id", 1)
    service_name = data.get("service_name", "Сервис")
    country_flag = data.get("country_flag", "🌍")
    country_name = data.get("country_name", "Страна")

    await state.update_data(rent_type=rent_type)

    if rent_type == "activation":
        # Сразу показываем подтверждение
        price = _calculate_price(service_code, country_id, "activation")
        await state.update_data(price=price, duration=None)
        await state.set_state(RentStates.confirming)

        text = Texts.confirm_rent(service_name, country_flag, country_name, "activation", None, price)
        await _answer_or_edit(query, text, confirm_kb(price))
    elif rent_type == "rent":
        # Выбор длительности
        await state.set_state(RentStates.choosing_duration)

        country = _get_country_by_id(country_id)
        price_per_hour = country["price_per_hour"] if country else 0.20

        text = Texts.select_duration(service_name, country_flag, country_name, price_per_hour)
        await _answer_or_edit(query, text, duration_selection_kb())

    await query.answer()


# ─── Выбор длительности ────────────────────────────────────────────────

@router.callback_query(F.data.startswith("duration:"), StateFilter(RentStates.choosing_duration))
async def cb_duration_selected(query: CallbackQuery, state: FSMContext, **kwargs):
    """Обрабатывает выбор длительности аренды."""
    try:
        duration = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        await query.answer("❌ Некорректная длительность", show_alert=True)
        return

    data = await state.get_data()
    service_code = data.get("service_code", "tg")
    country_id = data.get("country_id", 1)
    service_name = data.get("service_name", "Сервис")
    country_flag = data.get("country_flag", "🌍")
    country_name = data.get("country_name", "Страна")

    price = _calculate_price(service_code, country_id, "rent", duration)
    await state.update_data(duration=duration, price=price)
    await state.set_state(RentStates.confirming)

    text = Texts.confirm_rent(service_name, country_flag, country_name, "rent", duration, price)
    await _answer_or_edit(query, text, confirm_kb(price))
    await query.answer()


# ─── Подтверждение аренды ─────────────────────────────────────────────

@router.callback_query(F.data == "confirm_rent", StateFilter(RentStates.confirming))
async def cb_confirm_rent(query: CallbackQuery, state: FSMContext, **kwargs):
    """Подтверждает аренду и запускает её."""
    user_id = kwargs.get("user_id", query.from_user.id)
    data = await state.get_data()

    service_code = data.get("service_code", "tg")
    service_name = data.get("service_name", "Сервис")
    country_id = data.get("country_id", 1)
    country_name = data.get("country_name", "Страна")
    country_flag = data.get("country_flag", "🌍")
    rent_type = data.get("rent_type", "activation")
    duration = data.get("duration")
    price = data.get("price", 0.0)

    # Проверка баланса (заглушка)
    balance = await _stub_get_user_balance(user_id)
    if balance < price:
        text = Texts.insufficient_balance(balance, price)
        await _answer_or_edit(query, text, balance_kb())
        await query.answer("❌ Недостаточно средств", show_alert=True)
        return

    # Создание аренды (заглушка)
    rent = await _stub_create_rent(
        user_id=user_id,
        service_code=service_code,
        service_name=service_name,
        country_id=country_id,
        country_name=country_name,
        country_flag=country_flag,
        rent_type=rent_type,
        duration=duration,
        price=price,
    )

    # Сохраняем ID аренды в state
    await state.update_data(rent_id=rent["id"])
    await state.set_state(RentStates.waiting_for_sms)

    # Показываем карточку аренды
    time_left = _format_time_left(rent["expires_at"])
    text = Texts.rent_card(
        rent_id=rent["id"],
        phone=rent["phone"],
        service_name=rent["service_name"],
        country_flag=rent["country_flag"],
        country_name=rent["country_name"],
        rent_type=rent["rent_type"],
        time_left=time_left,
        price=rent["price"],
        sms_list=rent["sms"],
    )

    # Сначала успешное уведомление, потом карточка
    success_text = Texts.rent_success(rent["id"], rent["phone"])
    try:
        await query.message.edit_text(
            success_text,
            parse_mode="HTML",
        )
    except Exception:
        await query.message.answer(
            success_text,
            parse_mode="HTML",
        )

    await query.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=rent_control_kb(rent["id"]),
    )
    await query.answer("✅ Аренда начата!", show_alert=False)


# ─── Управление арендами ──────────────────────────────────────────────

@router.callback_query(F.data == "my_rents")
async def cb_my_rents(query: CallbackQuery, **kwargs):
    """Показывает список активных аренд пользователя."""
    user_id = kwargs.get("user_id", query.from_user.id)
    rents = await _stub_get_active_rents(user_id)

    if not rents:
        text = Texts.my_rents_empty()
        await _answer_or_edit(query, text, back_main_kb())
    else:
        # Строим список
        lines = []
        for r in rents:
            emoji = "📱"
            lines.append(
                Texts.rent_list_item(emoji, r["id"], r["phone"], r["service_name"])
            )
        rents_info = "\n".join(lines)
        text = Texts.my_rents_list(rents_info)
        await _answer_or_edit(query, text, my_rents_kb(rents))

    await query.answer()


@router.callback_query(F.data.startswith("rent_detail:"))
async def cb_rent_detail(query: CallbackQuery, **kwargs):
    """Показывает детали конкретной аренды."""
    try:
        rent_id = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        await query.answer("❌ Некорректный ID", show_alert=True)
        return

    rent = await _stub_get_rent(rent_id)
    if not rent or not rent["is_active"]:
        text = Texts.rent_not_found()
        await _answer_or_edit(query, text, back_main_kb())
        await query.answer()
        return

    time_left = _format_time_left(rent["expires_at"])
    text = Texts.rent_card(
        rent_id=rent["id"],
        phone=rent["phone"],
        service_name=rent["service_name"],
        country_flag=rent["country_flag"],
        country_name=rent["country_name"],
        rent_type=rent["rent_type"],
        time_left=time_left,
        price=rent["price"],
        sms_list=rent["sms"],
    )

    await _answer_or_edit(query, text, rent_control_kb(rent_id))
    await query.answer()


# ─── SMS ───────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("get_sms:"))
async def cb_get_sms(query: CallbackQuery, **kwargs):
    """Проверяет SMS для аренды."""
    try:
        rent_id = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        await query.answer("❌ Некорректный ID", show_alert=True)
        return

    sms_list = await _stub_check_sms(rent_id)
    text = Texts.sms_received(sms_list)

    rent = await _stub_get_rent(rent_id)
    if rent and rent["is_active"]:
        await _answer_or_edit(query, text, rent_control_kb(rent_id))
    else:
        await _answer_or_edit(query, text, back_main_kb())

    await query.answer()


# ─── Отмена аренды ────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("cancel_rent:"))
async def cb_cancel_rent(query: CallbackQuery, **kwargs):
    """Отменяет аренду."""
    user_id = kwargs.get("user_id", query.from_user.id)
    try:
        rent_id = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        await query.answer("❌ Некорректный ID", show_alert=True)
        return

    success = await _stub_cancel_rent(rent_id, user_id)
    if success:
        text = Texts.rent_cancelled(rent_id)
        await _answer_or_edit(query, text, back_main_kb())
        await query.answer("❌ Аренда отменена", show_alert=True)
    else:
        await query.answer("❌ Не удалось отменить аренду", show_alert=True)


# ─── Продление аренды ─────────────────────────────────────────────────

@router.callback_query(F.data.startswith("extend_rent:"))
async def cb_extend_rent(query: CallbackQuery, **kwargs):
    """Показывает варианты продления аренды."""
    try:
        rent_id = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        await query.answer("❌ Некорректный ID", show_alert=True)
        return

    rent = await _stub_get_rent(rent_id)
    if not rent or not rent["is_active"]:
        text = Texts.rent_not_found()
        await _answer_or_edit(query, text, back_main_kb())
        await query.answer()
        return

    text = (
        f"🔄 <b>Продление аренды #{rent_id}</b>\n\n"
        f"📱 {rent['phone']}\n"
        f"⏱ Текущий срок до: {_format_time_left(rent['expires_at'])}\n\n"
        f"{Texts.SEPARATOR}\n"
        f"Выберите срок продления 👇"
    )
    await _answer_or_edit(query, text, extend_duration_kb(rent_id))
    await query.answer()


@router.callback_query(F.data.startswith("extend_confirm:"))
async def cb_extend_confirm(query: CallbackQuery, **kwargs):
    """Подтверждает продление аренды."""
    user_id = kwargs.get("user_id", query.from_user.id)
    parts = query.data.split(":")

    try:
        rent_id = int(parts[1])
        extra_hours = int(parts[2])
    except (ValueError, IndexError):
        await query.answer("❌ Некорректные данные", show_alert=True)
        return

    new_expiry = await _stub_extend_rent(rent_id, user_id, extra_hours)
    if new_expiry:
        text = Texts.rent_extended(rent_id, new_expiry)
        await _answer_or_edit(query, text, rent_control_kb(rent_id))
        await query.answer("✅ Аренда продлена!", show_alert=True)
    else:
        await query.answer("❌ Не удалось продлить аренду", show_alert=True)


# ─── Баланс ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "balance")
async def cb_balance(query: CallbackQuery, **kwargs):
    """Показывает баланс пользователя."""
    user_id = kwargs.get("user_id", query.from_user.id)
    balance = await _stub_get_user_balance(user_id)
    total_spent = await _stub_get_user_total_spent(user_id)

    text = Texts.balance_show(balance, total_spent)
    await _answer_or_edit(query, text, balance_kb())
    await query.answer()


@router.callback_query(F.data == "topup")
async def cb_topup(query: CallbackQuery, state: FSMContext, **kwargs):
    """Начинает процесс пополнения баланса."""
    await state.set_state(TopUpStates.waiting_for_amount)

    text = Texts.topup_prompt()
    await _answer_or_edit(query, text, topup_kb())
    await query.answer()


@router.callback_query(F.data.startswith("topup_amount:"))
async def cb_topup_amount(query: CallbackQuery, state: FSMContext, **kwargs):
    """Обрабатывает выбор быстрой суммы пополнения."""
    try:
        amount = float(query.data.split(":")[1])
    except (ValueError, IndexError):
        await query.answer("❌ Некорректная сумма", show_alert=True)
        return

    if amount < 1.0 or amount > 500.0:
        await query.answer("❌ Сумма от $1.00 до $500.00", show_alert=True)
        return

    await state.clear()

    # Заглушка: обновляем баланс
    text = Texts.topup_success(amount, amount)
    await _answer_or_edit(query, text, back_main_kb())
    await query.answer(f"✅ Баланс пополнен на ${amount:.2f}!", show_alert=True)


# ─── Обработка текстового ввода (пополнение) ──────────────────────────

@router.message(StateFilter(TopUpStates.waiting_for_amount))
async def msg_topup_amount(message: Message, state: FSMContext, **kwargs):
    """Обрабатывает ввод суммы пополнения вручную."""
    try:
        amount = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer(Texts.topup_invalid_amount(), reply_markup=topup_kb())
        return

    if amount < 1.0 or amount > 500.0:
        await message.answer(Texts.topup_invalid_amount(), reply_markup=topup_kb())
        return

    await state.clear()

    # Заглушка: обновляем баланс
    text = Texts.topup_success(amount, amount)
    await message.answer(text, reply_markup=back_main_kb())


# ─── Навигация назад ──────────────────────────────────────────────────

@router.callback_query(F.data == "back")
async def cb_back(query: CallbackQuery, state: FSMContext, **kwargs):
    """Универсальная кнопка 'Назад' с учётом текущего состояния."""
    current_state = await state.get_state()
    data = await state.get_data()

    if current_state == RentStates.choosing_country:
        # Назад к выбору сервиса
        await state.set_state(RentStates.choosing_service)
        text = Texts.select_service()
        await _answer_or_edit(query, text, service_selection_kb())

    elif current_state == RentStates.choosing_rent_type:
        # Назад к выбору страны
        await state.set_state(RentStates.choosing_country)
        service_name = data.get("service_name", "Сервис")
        page = data.get("country_page", 0)
        text = Texts.select_country(service_name)
        await _answer_or_edit(query, text, country_selection_kb(page=page))

    elif current_state in (RentStates.choosing_duration, RentStates.confirming):
        rent_type = data.get("rent_type")
        service_name = data.get("service_name", "Сервис")
        country_flag = data.get("country_flag", "🌍")
        country_name = data.get("country_name", "Страна")
        country_id = data.get("country_id", 1)

        if rent_type == "rent":
            # Назад к выбору длительности или типу аренды
            if current_state == RentStates.confirming:
                await state.set_state(RentStates.choosing_duration)
                country = _get_country_by_id(country_id)
                price_per_hour = country["price_per_hour"] if country else 0.20
                text = Texts.select_duration(service_name, country_flag, country_name, price_per_hour)
                await _answer_or_edit(query, text, duration_selection_kb())
            else:
                await state.set_state(RentStates.choosing_rent_type)
                text = Texts.select_rent_type(service_name, country_flag, country_name)
                await _answer_or_edit(query, text, rent_type_kb())
        else:
            # activation — назад к выбору типа
            await state.set_state(RentStates.choosing_rent_type)
            text = Texts.select_rent_type(service_name, country_flag, country_name)
            await _answer_or_edit(query, text, rent_type_kb())

    elif current_state == TopUpStates.waiting_for_amount:
        # Назад из пополнения
        await state.clear()
        user_id = kwargs.get("user_id", query.from_user.id)
        username = kwargs.get("username", query.from_user.username or f"user_{user_id}")
        active_rents = await _stub_get_active_rents(user_id)
        balance = await _stub_get_user_balance(user_id)
        text = Texts.main_menu(username, balance, len(active_rents))
        await _answer_or_edit(query, text, main_menu_kb())

    else:
        # По умолчанию — главное меню
        user_id = kwargs.get("user_id", query.from_user.id)
        username = kwargs.get("username", query.from_user.username or f"user_{user_id}")
        active_rents = await _stub_get_active_rents(user_id)
        balance = await _stub_get_user_balance(user_id)
        await _show_main_menu(query, username, balance, len(active_rents), state)

    await query.answer()


# ─── Отмена ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "cancel")
async def cb_cancel(query: CallbackQuery, state: FSMContext, **kwargs):
    """Отменяет текущую операцию и возвращает в главное меню."""
    user_id = kwargs.get("user_id", query.from_user.id)
    username = kwargs.get("username", query.from_user.username or f"user_{user_id}")
    active_rents = await _stub_get_active_rents(user_id)
    balance = await _stub_get_user_balance(user_id)

    await _show_main_menu(query, username, balance, len(active_rents), state)
    await query.answer("❌ Операция отменена")


# ─── No-op (заглушка для пагинации) ───────────────────────────────────

@router.callback_query(F.data == "noop")
async def cb_noop(query: CallbackQuery, **kwargs):
    """Заглушка для некликабельных кнопок."""
    await query.answer()


# ─── Обработка сообщений по умолчанию ────────────────────────────────

@router.message(IsPrivateChat())
async def msg_default(message: Message, **kwargs):
    """Обрабатывает любые сообщения вне FSM."""
    await message.answer(
        "❓ Используйте команды из меню.",
        reply_markup=main_menu_kb(),
    )
