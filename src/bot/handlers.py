"""
Обработчики команд и callback'ов Telegram бота.
Использует реальный RentService (через data['rent_service']).
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    Message,
)

from src.api.hero_client import InsufficientBalanceError, NoNumbersError
from src.bot.filters import IsPrivateChat
from src.bot.icons import (
    ARROW_L, ARROW_R, BULLET, CHECK, CLOCK, COIN, CROSS, CROWN,
    DIAMOND, FLAG, GLOBE, GRID, HELP, HOME, LIST, MAIL, MENU,
    PHONE, REFRESH, SEARCH, SEP_THICK, SEP_THIN, SERVICE_ICONS,
    STAR, STATUS_ACTIVE, STATUS_INACTIVE, STATUS_WAITING, TOOL,
    get_service_icon, SEP_DOTS,
)
from src.bot.keyboards import (
    COUNTRIES,
    ITEMS_PER_PAGE,
    SERVICES,
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
from src.services.rent import RentService

logger = logging.getLogger(__name__)

router = Router()


# ─── Вспомогательные функции ──────────────────────────────────────────

def _get_rent_service(data: dict) -> RentService:
    """Получить RentService из data."""
    rs = data.get("rent_service")
    if rs is None:
        raise RuntimeError("RentService не инициализирован")
    return rs


def _calc_time_left(expires_at_str: Optional[str]) -> str:
    """Красивый таймер до истечения аренды."""
    if not expires_at_str:
        return "—"

    try:
        expires = datetime.fromisoformat(expires_at_str)
        now = datetime.utcnow()
        delta = expires - now

        if delta.total_seconds() <= 0:
            return f"{CROSS} Истекло"

        total_minutes = int(delta.total_seconds() / 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60

        if hours >= 24:
            days = hours // 24
            h = hours % 24
            return f"{days}д {h}ч {minutes}мин"
        elif hours > 0:
            return f"{hours}ч {minutes}мин"
        else:
            return f"{minutes}мин"
    except (ValueError, TypeError):
        return "—"


def _format_sms_list(sms_list: list) -> str:
    """Форматирует список SMS для отображения."""
    if not sms_list:
        return f"{CLOCK} Ожидание SMS..."

    lines = []
    for i, sms in enumerate(sms_list, 1):
        if hasattr(sms, "text"):
            text = sms.text
            code = sms.code or ""
        elif isinstance(sms, dict):
            text = sms.get("text", str(sms))
            code = sms.get("code", "")
        else:
            text = str(sms)
            code = ""

        display = f"{PHONE} {code}" if code else f"{MAIL} {text[:40]}"
        lines.append(f"  {BULLET} {display}")

    return "\n".join(lines) if lines else f"{CLOCK} Ожидание SMS..."


async def _answer_or_edit(
    event: Message | CallbackQuery,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
) -> Optional[Message]:
    """Отправить или отредактировать сообщение."""
    if isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )
        except Exception:
            await event.message.delete()
            return await event.message.answer(
                text,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )
        return None
    else:
        return await event.answer(
            text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )


async def _show_main_menu(
    event: Message | CallbackQuery,
    username: str,
    balance: float,
    active_count: int,
    state: FSMContext,
):
    """Показать главное меню и сбросить FSM."""
    await state.clear()
    text = Texts.main_menu(username, balance, active_count)
    await _answer_or_edit(event, text, main_menu_kb())


# ─── Команды ──────────────────────────────────────────────────────────

@router.message(Command("start"), IsPrivateChat())
async def cmd_start(message: Message, state: FSMContext, **kwargs):
    """Обработчик команды /start."""
    await state.clear()

    # Создаём/загружаем пользователя (выдаётся тестовый баланс $10)
    try:
        rs = _get_rent_service(kwargs)
        user_id = kwargs.get("user_id", message.from_user.id)
        username = kwargs.get("username", message.from_user.username or f"user_{user_id}")
        await rs.get_or_create_user(user_id, username)
    except Exception as exc:
        logger.warning(f"Не удалось создать пользователя: {exc}")

    text = Texts.welcome_new()
    await message.answer(text, reply_markup=main_menu_kb())


@router.message(Command("help"), IsPrivateChat())
async def cmd_help(message: Message, **kwargs):
    """Обработчик команды /help."""
    text = Texts.help_text()
    await message.answer(text, reply_markup=back_main_kb())


# ─── Главное меню ─────────────────────────────────────────────────────

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(query: CallbackQuery, state: FSMContext, **kwargs):
    """Возвращает в главное меню."""
    user_id = kwargs.get("user_id", query.from_user.id)
    username = kwargs.get("username", query.from_user.username or f"user_{user_id}")

    try:
        rs = _get_rent_service(kwargs)
        balance = await rs.get_user_balance(user_id)
        rents = await rs.get_active_rents(user_id)
        active_count = len(rents)
    except Exception:
        balance = 0.0
        active_count = 0

    await _show_main_menu(query, username, balance, active_count, state)
    await query.answer()


@router.callback_query(F.data == "help")
async def cb_help(query: CallbackQuery, **kwargs):
    """Показывает справку."""
    text = Texts.help_text()
    await _answer_or_edit(query, text, back_main_kb())
    await query.answer()


# ─── Начало аренды — выбор сервиса ────────────────────────────────────

@router.callback_query(F.data == "rent")
async def cb_rent_start(query: CallbackQuery, state: FSMContext, **kwargs):
    """Начинает процесс аренды."""
    await state.set_state(RentStates.choosing_service)
    await state.update_data(service_page=0)
    text = Texts.select_service()
    await _answer_or_edit(query, text, service_selection_kb())
    await query.answer()


@router.callback_query(F.data == "other_service")
async def cb_other_service(query: CallbackQuery, state: FSMContext, **kwargs):
    """Переход к ручному вводу сервиса."""
    await state.set_state(RentStates.waiting_for_service_name)
    text = (
        f"{SEARCH} <b>Введите название сервиса</b>\n\n"
        f"Напишите название сервиса вручную.\n"
        f"Например: <code>Telegram</code>, <code>WhatsApp</code>, <code>Instagram</code>\n\n"
        f"{SEP_THIN}"
    )
    await _answer_or_edit(query, text, cancel_kb())
    await query.answer()


# ─── Выбор сервиса ────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("service:"), StateFilter(RentStates.choosing_service))
async def cb_service_selected(query: CallbackQuery, state: FSMContext, **kwargs):
    """Обрабатывает выбор сервиса из списка."""
    code = query.data.split(":")[1]
    service = next((s for s in SERVICES if s["code"] == code), None)
    if not service:
        await query.answer(f"{CROSS} Сервис не найден", show_alert=True)
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


# ─── Ручной ввод названия сервиса ─────────────────────────────────────

@router.message(StateFilter(RentStates.waiting_for_service_name))
async def msg_service_name(message: Message, state: FSMContext, **kwargs):
    """Обрабатывает ввод названия сервиса вручную."""
    name = message.text.strip()
    if len(name) > 30:
        await message.answer(
            f"{CROSS} Слишком длинное название. Максимум 30 символов.",
            reply_markup=cancel_kb(),
        )
        return

    # Ищем в списке сервисов
    matched = None
    for s in SERVICES:
        if s["name"].lower() == name.lower():
            matched = s
            break

    if matched:
        code = matched["code"]
    else:
        # Используем код "other" с пользовательским названием
        code = "other"

    await state.update_data(
        service_code=code,
        service_name=name,
        country_page=0,
    )
    await state.set_state(RentStates.choosing_country)

    text = Texts.select_country(name)
    await _answer_or_edit(message, text, country_selection_kb(page=0))


# ─── Выбор страны ─────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("country:"), StateFilter(RentStates.choosing_country))
async def cb_country_selected(query: CallbackQuery, state: FSMContext, **kwargs):
    """Обрабатывает выбор страны."""
    try:
        country_id = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        await query.answer(f"{CROSS} Некорректный выбор", show_alert=True)
        return

    country = next((c for c in COUNTRIES if c["id"] == country_id), None)
    if not country:
        await query.answer(f"{GLOBE} Страна не найдена", show_alert=True)
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


# ─── Выбор типа аренды ────────────────────────────────────────────────

@router.callback_query(F.data.startswith("rent_type:"), StateFilter(RentStates.choosing_rent_type))
async def cb_rent_type_selected(query: CallbackQuery, state: FSMContext, **kwargs):
    """Обрабатывает выбор типа."""
    rent_type = query.data.split(":")[1]
    data = await state.get_data()

    await state.update_data(rent_type=rent_type)

    if rent_type == "activation":
        price = _calc_price(data, "activation")
        await state.update_data(price=price, duration=None)
        await state.set_state(RentStates.confirming)

        text = Texts.confirm_rent(
            data.get("service_name", ""),
            data.get("country_flag", ""),
            data.get("country_name", ""),
            "activation", None, price,
        )
        await _answer_or_edit(query, text, confirm_kb(price))
    elif rent_type == "rent":
        await state.set_state(RentStates.choosing_duration)

        country_id = data.get("country_id", 1)
        country = next((c for c in COUNTRIES if c["id"] == country_id), None)
        price_per_hour = country["price_per_hour"] if country else 0.20

        text = Texts.select_duration(
            data.get("service_name", ""),
            data.get("country_flag", ""),
            data.get("country_name", ""),
            price_per_hour,
        )
        await _answer_or_edit(query, text, duration_selection_kb())

    await query.answer()


# ─── Выбор длительности ───────────────────────────────────────────────

@router.callback_query(F.data.startswith("duration:"), StateFilter(RentStates.choosing_duration))
async def cb_duration_selected(query: CallbackQuery, state: FSMContext, **kwargs):
    """Обрабатывает выбор длительности."""
    try:
        duration = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        await query.answer(f"{CROSS} Некорректная длительность", show_alert=True)
        return

    data = await state.get_data()
    price = _calc_price(data, "rent", duration)

    await state.update_data(duration=duration, price=price)
    await state.set_state(RentStates.confirming)

    text = Texts.confirm_rent(
        data.get("service_name", ""),
        data.get("country_flag", ""),
        data.get("country_name", ""),
        "rent", duration, price,
    )
    await _answer_or_edit(query, text, confirm_kb(price))
    await query.answer()


# ─── Подтверждение аренды ─────────────────────────────────────────────

@router.callback_query(F.data == "confirm_rent", StateFilter(RentStates.confirming))
async def cb_confirm_rent(query: CallbackQuery, state: FSMContext, **kwargs):
    """Подтверждает аренду и запускает её через RentService."""
    user_id = kwargs.get("user_id", query.from_user.id)
    data = await state.get_data()

    try:
        rs = _get_rent_service(kwargs)

        # Регистрируем пользователя
        username = kwargs.get("username", f"user_{user_id}")
        await rs.get_or_create_user(user_id, username)

        service_code = data.get("service_code", "other")
        service_name = data.get("service_name", "Сервис")
        country_id = data.get("country_id", 1)
        country_name = data.get("country_name", "Страна")
        rent_type = data.get("rent_type", "activation")
        duration = data.get("duration")

        if rent_type == "activation":
            rent = await rs.start_activation(
                telegram_id=user_id,
                service=service_code,
                country=country_id,
                service_name=service_name,
                country_name=country_name,
            )
            rent_id = rent.id
            phone = rent.phone
        else:
            rent = await rs.start_rent(
                telegram_id=user_id,
                service=service_code,
                country=country_id,
                hours=duration or 4,
                service_name=service_name,
                country_name=country_name,
            )
            rent_id = rent.id
            phone = rent.phone

        await state.update_data(rent_id=rent_id)
        await state.set_state(RentStates.waiting_for_sms)

        # Сообщение об успехе
        success_text = (
            f"{CHECK} <b>Аренда успешно начата!</b>\n\n"
            f"{SEP_THICK}\n"
            f"{PHONE} <b>Номер:</b> <code>{phone}</code>\n"
            f"{BULLET} <b>ID:</b> {rent_id}\n"
            f"{SEP_THICK}\n\n"
            f"{CLOCK} Ожидайте SMS на указанный номер."
        )

        try:
            await query.message.edit_text(success_text, parse_mode="HTML")
        except Exception:
            await query.message.answer(success_text, parse_mode="HTML")

        # Карточка аренды
        time_left = _calc_time_left(
            rent.expires_at.isoformat() if hasattr(rent, 'expires_at') and rent.expires_at else None
        )
        sms_list = await rs.check_sms(rent_id) if hasattr(rs, 'check_sms') else []

        card_text = Texts.rent_card(
            rent_id=rent.id,
            phone=rent.phone,
            service_name=service_name,
            country_flag=data.get("country_flag", ""),
            country_name=country_name,
            rent_type=rent_type,
            time_left=time_left,
            price=float(getattr(rent, 'price', 0) or 0),
            sms_list=[s.text if hasattr(s, 'text') else str(s) for s in sms_list],
        )
        await query.message.answer(
            card_text,
            parse_mode="HTML",
            reply_markup=rent_control_kb(rent.id),
        )
        await query.answer(f"{CHECK} Аренда начата!")

    except InsufficientBalanceError:
        balance = await rs.get_user_balance(user_id) if 'rs' in locals() else 0
        price = data.get("price", 0)
        text = Texts.insufficient_balance(balance, price)
        await _answer_or_edit(query, text, balance_kb())
        await query.answer(f"{CROSS} Недостаточно средств", show_alert=True)

    except NoNumbersError:
        text = (
            f"{CROSS} <b>Нет доступных номеров</b>\n\n"
            f"Попробуйте выбрать другую страну или сервис.\n"
            f"{SEP_THIN}"
        )
        await _answer_or_edit(query, text, back_main_kb())
        await query.answer(f"{CROSS} Нет номеров", show_alert=True)

    except Exception as exc:
        logger.exception(f"Ошибка аренды: {exc}")
        text = (
            f"{CROSS} <b>Ошибка при аренде</b>\n\n"
            f"Проверьте баланс и попробуйте снова.\n"
            f"{SEP_THIN}"
        )
        await _answer_or_edit(query, text, back_main_kb())
        await query.answer(f"{CROSS} Ошибка", show_alert=True)


# ─── Мои аренды ───────────────────────────────────────────────────────

@router.callback_query(F.data == "my_rents")
async def cb_my_rents(query: CallbackQuery, **kwargs):
    """Показывает список активных аренд."""
    user_id = kwargs.get("user_id", query.from_user.id)

    try:
        rs = _get_rent_service(kwargs)
        rents = await rs.get_active_rents(user_id)
    except Exception:
        rents = []

    if not rents:
        text = Texts.my_rents_empty()
        await _answer_or_edit(query, text, back_main_kb())
    else:
        lines = []
        for r in rents:
            phone = getattr(r, 'phone', '—')
            s_name = getattr(r, 'service_name', '—')
            lines.append(f"  {PHONE} <b>#{r.id}</b> {phone} — {s_name}")

        text = (
            f"{LIST} <b>Мои аренды</b>\n\n"
            + "\n".join(lines) + "\n\n"
            + f"{SEP_THIN}\n"
            f"Выберите аренду для управления {ARROW_R}"
        )
        await _answer_or_edit(query, text, my_rents_kb(rents))

    await query.answer()


@router.callback_query(F.data.startswith("rent_detail:"))
async def cb_rent_detail(query: CallbackQuery, **kwargs):
    """Показывает детали аренды."""
    try:
        rent_id = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        await query.answer(f"{CROSS} Некорректный ID", show_alert=True)
        return

    try:
        rs = _get_rent_service(kwargs)
        rent = await rs.get_rent_detail(rent_id)
    except Exception:
        rent = None

    if not rent or getattr(rent, 'status', '') in ('cancelled', 'expired'):
        text = Texts.rent_not_found()
        await _answer_or_edit(query, text, back_main_kb())
        await query.answer()
        return

    sms_list = _load_sms_list(rent)
    time_left = _calc_time_left(
        rent.expires_at.isoformat() if hasattr(rent, 'expires_at') and rent.expires_at else None
    )

    text = Texts.rent_card(
        rent_id=rent.id,
        phone=getattr(rent, 'phone', '—'),
        service_name=getattr(rent, 'service_name', '—'),
        country_flag="",
        country_name=getattr(rent, 'country', '—'),
        rent_type=getattr(rent, 'rent_type', 'activation'),
        time_left=time_left,
        price=float(getattr(rent, 'price', 0) or 0),
        sms_list=sms_list,
    )

    await _answer_or_edit(query, text, rent_control_kb(rent_id))
    await query.answer()


def _load_sms_list(rent) -> list[str]:
    """Загрузить SMS из объекта аренды."""
    try:
        if hasattr(rent, 'sms_messages') and rent.sms_messages:
            return [s.text if hasattr(s, 'text') else str(s) for s in rent.sms_messages]
    except Exception:
        pass
    return []


# ─── SMS ──────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("get_sms:"))
async def cb_get_sms(query: CallbackQuery, **kwargs):
    """Проверяет SMS для аренды."""
    try:
        rent_id = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        await query.answer(f"{CROSS} Некорректный ID", show_alert=True)
        return

    try:
        rs = _get_rent_service(kwargs)
        sms_messages = await rs.check_sms(rent_id)

        if sms_messages:
            sms_list = [s.text if hasattr(s, 'text') else str(s) for s in sms_messages]
        else:
            sms_list = []

    except Exception:
        sms_list = []

    text = Texts.sms_received(sms_list)

    try:
        rent = await rs.get_rent_detail(rent_id)
        is_active = rent and getattr(rent, 'status', '') not in ('cancelled', 'expired')
    except Exception:
        is_active = False

    await _answer_or_edit(query, text, rent_control_kb(rent_id) if is_active else back_main_kb())
    await query.answer()


# ─── Отмена аренды ────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("cancel_rent:"))
async def cb_cancel_rent(query: CallbackQuery, **kwargs):
    """Отменяет аренду."""
    user_id = kwargs.get("user_id", query.from_user.id)
    try:
        rent_id = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        await query.answer(f"{CROSS} Некорректный ID", show_alert=True)
        return

    try:
        rs = _get_rent_service(kwargs)
        success = await rs.cancel_rent(rent_id, user_id)
    except Exception:
        success = False

    if success:
        text = (
            f"{CROSS} <b>Аренда #{rent_id} отменена</b>\n\n"
            f"Средства возвращены на баланс.\n"
            f"{SEP_THIN}"
        )
        await _answer_or_edit(query, text, back_main_kb())
        await query.answer(f"{CROSS} Аренда отменена", show_alert=True)
    else:
        await query.answer(f"{CROSS} Не удалось отменить аренду", show_alert=True)


# ─── Продление аренды ─────────────────────────────────────────────────

@router.callback_query(F.data.startswith("extend_rent:"))
async def cb_extend_rent(query: CallbackQuery, **kwargs):
    """Показывает варианты продления."""
    try:
        rent_id = int(query.data.split(":")[1])
    except (ValueError, IndexError):
        await query.answer(f"{CROSS} Некорректный ID", show_alert=True)
        return

    try:
        rs = _get_rent_service(kwargs)
        rent = await rs.get_rent_detail(rent_id)
    except Exception:
        rent = None

    if not rent or getattr(rent, 'status', '') in ('cancelled', 'expired'):
        text = Texts.rent_not_found()
        await _answer_or_edit(query, text, back_main_kb())
        await query.answer()
        return

    time_left = _calc_time_left(
        rent.expires_at.isoformat() if hasattr(rent, 'expires_at') and rent.expires_at else None
    )

    text = (
        f"{REFRESH} <b>Продление аренды #{rent_id}</b>\n\n"
        f"{PHONE} {getattr(rent, 'phone', '—')}\n"
        f"{CLOCK} Текущий срок: {time_left}\n\n"
        f"{SEP_THIN}\n"
        f"Выберите срок продления {ARROW_R}"
    )
    await _answer_or_edit(query, text, extend_duration_kb(rent_id))
    await query.answer()


@router.callback_query(F.data.startswith("extend_confirm:"))
async def cb_extend_confirm(query: CallbackQuery, **kwargs):
    """Подтверждает продление."""
    user_id = kwargs.get("user_id", query.from_user.id)
    parts = query.data.split(":")
    try:
        rent_id = int(parts[1])
        extra_hours = int(parts[2])
    except (ValueError, IndexError):
        await query.answer(f"{CROSS} Некорректные данные", show_alert=True)
        return

    try:
        rs = _get_rent_service(kwargs)
        new_expiry = await rs.extend_rent(rent_id, user_id, extra_hours)
    except Exception:
        new_expiry = None

    if new_expiry:
        expiry_str = new_expiry.strftime("%Y-%m-%d %H:%M") if hasattr(new_expiry, 'strftime') else str(new_expiry)
        text = (
            f"{CHECK} <b>Аренда #{rent_id} продлена</b>\n\n"
            f"{CLOCK} Новый срок: <b>{expiry_str}</b> UTC\n"
            f"{SEP_THIN}"
        )
        await _answer_or_edit(query, text, rent_control_kb(rent_id))
        await query.answer(f"{CHECK} Аренда продлена!", show_alert=True)
    else:
        await query.answer(f"{CROSS} Не удалось продлить", show_alert=True)


# ─── Баланс ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "balance")
async def cb_balance(query: CallbackQuery, **kwargs):
    """Показывает баланс."""
    user_id = kwargs.get("user_id", query.from_user.id)

    try:
        rs = _get_rent_service(kwargs)
        balance = await rs.get_user_balance(user_id)
        total_spent = await rs.get_total_spent(user_id)
    except Exception:
        balance = 0.0
        total_spent = 0.0

    text = Texts.balance_show(balance, total_spent)
    await _answer_or_edit(query, text, balance_kb())
    await query.answer()


@router.callback_query(F.data == "topup")
async def cb_topup(query: CallbackQuery, state: FSMContext, **kwargs):
    """Начинает процесс пополнения."""
    await state.set_state(TopUpStates.waiting_for_amount)
    text = Texts.topup_prompt()
    await _answer_or_edit(query, text, topup_kb())
    await query.answer()


@router.callback_query(F.data.startswith("topup_amount:"))
async def cb_topup_amount(query: CallbackQuery, state: FSMContext, **kwargs):
    """Быстрое пополнение."""
    try:
        amount = float(query.data.split(":")[1])
    except (ValueError, IndexError):
        await query.answer(f"{CROSS} Некорректная сумма", show_alert=True)
        return

    if amount < 1.0 or amount > 500.0:
        await query.answer(f"{CROSS} Сумма от $1.00 до $500.00", show_alert=True)
        return

    user_id = kwargs.get("user_id", query.from_user.id)

    try:
        rs = _get_rent_service(kwargs)
        new_balance = await rs.topup_balance(user_id, amount)
    except Exception:
        new_balance = amount

    await state.clear()
    text = Texts.topup_success(amount, new_balance)
    await _answer_or_edit(query, text, back_main_kb())
    await query.answer(f"{CHECK} Баланс пополнен на ${amount:.2f}!", show_alert=True)


@router.message(StateFilter(TopUpStates.waiting_for_amount))
async def msg_topup_amount(message: Message, state: FSMContext, **kwargs):
    """Ручной ввод суммы пополнения."""
    try:
        amount = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer(Texts.topup_invalid_amount(), reply_markup=topup_kb())
        return

    if amount < 1.0 or amount > 500.0:
        await message.answer(Texts.topup_invalid_amount(), reply_markup=topup_kb())
        return

    user_id = kwargs.get("user_id", message.from_user.id)

    try:
        rs = _get_rent_service(kwargs)
        new_balance = await rs.topup_balance(user_id, amount)
    except Exception:
        new_balance = amount

    await state.clear()
    text = Texts.topup_success(amount, new_balance)
    await message.answer(text, reply_markup=back_main_kb())


# ─── Навигация ────────────────────────────────────────────────────────

@router.callback_query(F.data == "back")
async def cb_back(query: CallbackQuery, state: FSMContext, **kwargs):
    """Универсальная кнопка 'Назад'."""
    current_state = await state.get_state()
    data = await state.get_data()

    if current_state == RentStates.choosing_country:
        await state.set_state(RentStates.choosing_service)
        text = Texts.select_service()
        await _answer_or_edit(query, text, service_selection_kb())

    elif current_state == RentStates.choosing_rent_type:
        await state.set_state(RentStates.choosing_country)
        service_name = data.get("service_name", "Сервис")
        page = data.get("country_page", 0)
        text = Texts.select_country(service_name)
        await _answer_or_edit(query, text, country_selection_kb(page=page))

    elif current_state in (RentStates.choosing_duration, RentStates.confirming):
        rent_type = data.get("rent_type")
        if rent_type == "rent" and current_state == RentStates.confirming:
            await state.set_state(RentStates.choosing_duration)
            country_id = data.get("country_id", 1)
            country = next((c for c in COUNTRIES if c["id"] == country_id), None)
            price_per_hour = country["price_per_hour"] if country else 0.20
            text = Texts.select_duration(
                data.get("service_name", ""),
                data.get("country_flag", ""),
                data.get("country_name", ""),
                price_per_hour,
            )
            await _answer_or_edit(query, text, duration_selection_kb())
        else:
            await state.set_state(RentStates.choosing_rent_type)
            text = Texts.select_rent_type(
                data.get("service_name", ""),
                data.get("country_flag", ""),
                data.get("country_name", ""),
            )
            await _answer_or_edit(query, text, rent_type_kb())

    elif current_state == TopUpStates.waiting_for_amount:
        await _back_to_main(query, state, kwargs)

    elif current_state == RentStates.waiting_for_service_name:
        await state.set_state(RentStates.choosing_service)
        text = Texts.select_service()
        await _answer_or_edit(query, text, service_selection_kb())

    else:
        await _back_to_main(query, state, kwargs)

    await query.answer()


@router.callback_query(F.data == "cancel")
async def cb_cancel(query: CallbackQuery, state: FSMContext, **kwargs):
    """Отменяет операцию."""
    await _back_to_main(query, state, kwargs)
    await query.answer(f"{CROSS} Операция отменена")


async def _back_to_main(event, state, kwargs):
    """Вернуться в главное меню."""
    user_id = kwargs.get("user_id", 0)
    username = kwargs.get("username", f"user_{user_id}")

    try:
        rs = _get_rent_service(kwargs)
        balance = await rs.get_user_balance(user_id)
        rents = await rs.get_active_rents(user_id)
        active_count = len(rents)
    except Exception:
        balance = 0.0
        active_count = 0

    await _show_main_menu(event, username, balance, active_count, state)


@router.callback_query(F.data == "noop")
async def cb_noop(query: CallbackQuery, **kwargs):
    """Заглушка для некликабельных кнопок."""
    await query.answer()


# ─── Обработка сообщений по умолчанию ─────────────────────────────────

@router.message(IsPrivateChat())
async def msg_default(message: Message, **kwargs):
    """Любые сообщения вне FSM."""
    await message.answer(
        f"{MENU} Используйте команды из меню.",
        reply_markup=main_menu_kb(),
    )


# ─── Расчёт цены ──────────────────────────────────────────────────────

def _calc_price(data: dict, rent_type: str, duration: int = None) -> float:
    """Рассчитать цену."""
    country_id = data.get("country_id", 1)
    country = next((c for c in COUNTRIES if c["id"] == country_id), None)

    if rent_type == "activation":
        return country["price_activation"] if country else 0.50
    elif rent_type == "rent" and duration:
        price_per_hour = country["price_per_hour"] if country else 0.20
        return round(price_per_hour * duration, 2)
    return 0.50
