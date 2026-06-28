"""
Премиальные inline-клавиатуры с кастомными черно-белыми иконками.
"""

from typing import Optional, Sequence

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.bot.icons import (
    ARROW_L, ARROW_R, CHECK, COIN, CROSS, CROWN, DIAMOND,
    GLOBE, GRID, HELP, HOME, KEY, LIST, MAIL, MENU, PHONE,
    PLUS, REFRESH, SEARCH, SEP_THIN, STAR, STATUS_ACTIVE,
    TOOL, get_service_icon, SEP_DOTS,
)
from src.db.models import Rent

# ─── Данные для клавиатур ──────────────────────────────────────────────

SERVICES: list[dict] = [
    {"code": "tg", "name": "Telegram", "icon": get_service_icon("tg")},
    {"code": "wa", "name": "WhatsApp", "icon": get_service_icon("wa")},
    {"code": "ig", "name": "Instagram", "icon": get_service_icon("ig")},
    {"code": "go", "name": "Google", "icon": get_service_icon("go")},
    {"code": "fb", "name": "Facebook", "icon": get_service_icon("fb")},
    {"code": "vb", "name": "Viber", "icon": get_service_icon("vb")},
    {"code": "ok", "name": "Odnoklassniki", "icon": get_service_icon("ok")},
    {"code": "tt", "name": "TikTok", "icon": get_service_icon("tt")},
    {"code": "tw", "name": "Twitter (X)", "icon": get_service_icon("tw")},
]

COUNTRIES: list[dict] = [
    {"id": 1, "name": "Россия", "flag": "🇷🇺", "code": "RU", "price_activation": 0.30, "price_per_hour": 0.15},
    {"id": 2, "name": "Украина", "flag": "🇺🇦", "code": "UA", "price_activation": 0.25, "price_per_hour": 0.12},
    {"id": 3, "name": "Казахстан", "flag": "🇰🇿", "code": "KZ", "price_activation": 0.20, "price_per_hour": 0.10},
    {"id": 4, "name": "США", "flag": "🇺🇸", "code": "US", "price_activation": 0.50, "price_per_hour": 0.25},
    {"id": 5, "name": "Великобритания", "flag": "🇬🇧", "code": "GB", "price_activation": 0.55, "price_per_hour": 0.28},
    {"id": 6, "name": "Германия", "flag": "🇩🇪", "code": "DE", "price_activation": 0.45, "price_per_hour": 0.22},
    {"id": 7, "name": "Франция", "flag": "🇫🇷", "code": "FR", "price_activation": 0.50, "price_per_hour": 0.25},
    {"id": 8, "name": "Испания", "flag": "🇪🇸", "code": "ES", "price_activation": 0.40, "price_per_hour": 0.20},
    {"id": 9, "name": "Италия", "flag": "🇮🇹", "code": "IT", "price_activation": 0.45, "price_per_hour": 0.22},
    {"id": 10, "name": "Нидерланды", "flag": "🇳🇱", "code": "NL", "price_activation": 0.48, "price_per_hour": 0.24},
    {"id": 11, "name": "Китай", "flag": "🇨🇳", "code": "CN", "price_activation": 0.60, "price_per_hour": 0.30},
    {"id": 12, "name": "Индия", "flag": "🇮🇳", "code": "IN", "price_activation": 0.15, "price_per_hour": 0.08},
    {"id": 13, "name": "Бразилия", "flag": "🇧🇷", "code": "BR", "price_activation": 0.35, "price_per_hour": 0.18},
    {"id": 14, "name": "Турция", "flag": "🇹🇷", "code": "TR", "price_activation": 0.28, "price_per_hour": 0.14},
    {"id": 15, "name": "Польша", "flag": "🇵🇱", "code": "PL", "price_activation": 0.38, "price_per_hour": 0.19},
    {"id": 16, "name": "Египет", "flag": "🇪🇬", "code": "EG", "price_activation": 0.22, "price_per_hour": 0.11},
    {"id": 17, "name": "Индонезия", "flag": "🇮🇩", "code": "ID", "price_activation": 0.18, "price_per_hour": 0.09},
    {"id": 18, "name": "Израиль", "flag": "🇮🇱", "code": "IL", "price_activation": 0.55, "price_per_hour": 0.28},
]

ITEMS_PER_PAGE = 6


# ─── Вспомогательные функции ───────────────────────────────────────────

def _btn(text: str, callback_data: str) -> InlineKeyboardButton:
    """Создать кнопку с callback_data."""
    return InlineKeyboardButton(text=text, callback_data=callback_data)


def _url(text: str, url: str) -> InlineKeyboardButton:
    """Создать кнопку-ссылку."""
    return InlineKeyboardButton(text=text, url=url)


# ─── Главное меню ─────────────────────────────────────────────────────

def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn(f"{PHONE} Арендовать", "rent"),
        _btn(f"{LIST} Мои аренды", "my_rents"),
        width=2,
    )
    builder.row(
        _btn(f"{COIN} Баланс", "balance"),
        _btn(f"{HELP} Помощь", "help"),
        width=2,
    )
    return builder.as_markup()


# ─── Выбор сервиса ─────────────────────────────────────────────────────

def service_selection_kb() -> InlineKeyboardMarkup:
    """Сетка сервисов по 3 в ряд + ручной ввод."""
    builder = InlineKeyboardBuilder()

    for i in range(0, len(SERVICES), 3):
        row = SERVICES[i:i + 3]
        buttons = [
            _btn(f"{s['icon']} {s['name']}", f"service:{s['code']}")
            for s in row
        ]
        builder.row(*buttons, width=3)

    builder.row(
        _btn(f"{SEARCH} Другой сервис", "other_service"),
        _btn(f"{HOME} Главная", "main_menu"),
        width=2,
    )

    return builder.as_markup()


# ─── Выбор страны ─────────────────────────────────────────────────────

def country_selection_kb(
    countries: Optional[list[dict]] = None,
    page: int = 0,
) -> InlineKeyboardMarkup:
    """Список стран с флагами и ценами, постранично."""
    if countries is None:
        countries = COUNTRIES

    total_pages = max(1, (len(countries) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_countries = countries[start:end]

    builder = InlineKeyboardBuilder()

    for c in page_countries:
        price_str = f"${c['price_activation']:.2f}"
        builder.row(
            _btn(
                f"{c['flag']} {c['name']}  {COIN} {price_str}",
                f"country:{c['id']}",
            ),
            width=1,
        )

    # Пагинация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(_btn(f"{ARROW_L}", f"country_page:{page - 1}"))

    nav_buttons.append(_btn(f"{page + 1}/{total_pages}", "noop"))

    if page < total_pages - 1:
        nav_buttons.append(_btn(f"{ARROW_R}", f"country_page:{page + 1}"))

    builder.row(*nav_buttons, width=len(nav_buttons))

    builder.row(
        _btn(f"{ARROW_L} Назад", "back"),
        _btn(f"{HOME} Главная", "main_menu"),
        width=2,
    )

    return builder.as_markup()


# ─── Выбор типа аренды ─────────────────────────────────────────────────

def rent_type_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn(f"{PHONE} Активация (20 мин)", "rent_type:activation"),
        width=1,
    )
    builder.row(
        _btn(f"{STAR} Аренда (от 4 часов)", "rent_type:rent"),
        width=1,
    )
    builder.row(
        _btn(f"{ARROW_L} Назад", "back"),
        _btn(f"{HOME} Главная", "main_menu"),
        width=2,
    )
    return builder.as_markup()


# ─── Выбор длительности ────────────────────────────────────────────────

def duration_selection_kb() -> InlineKeyboardMarkup:
    """Клавиатура выбора длительности."""
    durations = [
        (4, f"{CLOCK} 4 часа"),
        (12, f"{CLOCK} 12 часов"),
        (24, f"{CLOCK} 24 часа"),
        (72, f"{CLOCK} 3 дня"),
        (168, f"{CLOCK} 7 дней"),
        (336, f"{CLOCK} 14 дней"),
    ]

    builder = InlineKeyboardBuilder()

    for i in range(0, len(durations), 2):
        row = durations[i:i + 2]
        buttons = [_btn(label, f"duration:{hours}") for hours, label in row]
        builder.row(*buttons, width=2)

    builder.row(
        _btn(f"{ARROW_L} Назад", "back"),
        _btn(f"{HOME} Главная", "main_menu"),
        width=2,
    )

    return builder.as_markup()


# ─── Подтверждение ─────────────────────────────────────────────────────

def confirm_kb(price: float) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn(f"{CHECK} Подтвердить ${price:.2f}", "confirm_rent"),
        width=1,
    )
    builder.row(
        _btn(f"{ARROW_L} Назад", "back"),
        _btn(f"{HOME} Главная", "main_menu"),
        width=2,
    )
    return builder.as_markup()


# ─── Управление арендой ────────────────────────────────────────────────

def rent_control_kb(rent_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn(f"{MAIL} SMS", f"get_sms:{rent_id}"),
        _btn(f"{REFRESH} Продлить", f"extend_rent:{rent_id}"),
        width=2,
    )
    builder.row(
        _btn(f"{CROSS} Отменить", f"cancel_rent:{rent_id}"),
        _btn(f"{LIST} К списку", "my_rents"),
        width=2,
    )
    builder.row(
        _btn(f"{HOME} Главная", "main_menu"),
        width=1,
    )
    return builder.as_markup()


# ─── Баланс ────────────────────────────────────────────────────────────

def balance_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn(f"{PLUS} Пополнить", "topup"),
        _btn(f"{REFRESH} Обновить", "balance"),
        width=2,
    )
    builder.row(
        _btn(f"{HOME} Главная", "main_menu"),
        width=1,
    )
    return builder.as_markup()


# ─── Список моих аренд ─────────────────────────────────────────────────

def my_rents_kb(rents: Sequence) -> InlineKeyboardMarkup:
    """Клавиатура со списком аренд пользователя."""
    builder = InlineKeyboardBuilder()

    for rent in rents:
        phone = getattr(rent, 'phone', '—')
        s_name = getattr(rent, 'service_name', '—')
        builder.row(
            _btn(
                f"{PHONE} #{rent.id} {phone}  {s_name}",
                f"rent_detail:{rent.id}",
            ),
            width=1,
        )

    builder.row(
        _btn(f"{HOME} Главная", "main_menu"),
        width=1,
    )

    return builder.as_markup()


# ─── Простые клавиатуры ────────────────────────────────────────────────

def back_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_btn(f"{ARROW_L} Назад", "back"), width=1)
    return builder.as_markup()


def cancel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn(f"{CROSS} Отмена", "cancel"),
        width=1,
    )
    return builder.as_markup()


def back_main_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_btn(f"{HOME} Главное меню", "main_menu"), width=1)
    return builder.as_markup()


def topup_kb() -> InlineKeyboardMarkup:
    """Клавиатура с быстрыми суммами пополнения."""
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn(f"$5", "topup_amount:5"),
        _btn(f"$10", "topup_amount:10"),
        _btn(f"$25", "topup_amount:25"),
        _btn(f"$50", "topup_amount:50"),
        width=4,
    )
    builder.row(_btn(f"{CROSS} Отмена", "main_menu"), width=1)
    return builder.as_markup()


def extend_duration_kb(rent_id: int) -> InlineKeyboardMarkup:
    """Клавиатура продления с выбором срока."""
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn(f"{CLOCK} +4 ч", f"extend_confirm:{rent_id}:4"),
        _btn(f"{CLOCK} +12 ч", f"extend_confirm:{rent_id}:12"),
        _btn(f"{CLOCK} +24 ч", f"extend_confirm:{rent_id}:24"),
        width=3,
    )
    builder.row(
        _btn(f"{CLOCK} +3 д", f"extend_confirm:{rent_id}:72"),
        _btn(f"{CLOCK} +7 д", f"extend_confirm:{rent_id}:168"),
        width=2,
    )
    builder.row(
        _btn(f"{ARROW_L} Назад", f"rent_detail:{rent_id}"),
        _btn(f"{HOME} Главная", "main_menu"),
        width=2,
    )
    return builder.as_markup()
