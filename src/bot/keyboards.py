"""
Премиальные inline-клавиатуры с эмодзи.
Все функции возвращают InlineKeyboardMarkup.
"""

from typing import Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ─── Данные для клавиатур ──────────────────────────────────────────────

SERVICES: list[dict] = [
    {"code": "tg", "name": "Telegram", "emoji": "🔷"},
    {"code": "wa", "name": "WhatsApp", "emoji": "💬"},
    {"code": "ig", "name": "Instagram", "emoji": "📸"},
    {"code": "go", "name": "Google", "emoji": "▶️"},
    {"code": "fb", "name": "Facebook", "emoji": "👍"},
    {"code": "vb", "name": "Viber", "emoji": "📺"},
    {"code": "ok", "name": "Odnoklassniki", "emoji": "👥"},
    {"code": "tt", "name": "TikTok", "emoji": "🎵"},
    {"code": "tw", "name": "Twitter (X)", "emoji": "🐦"},
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

def _build_url_button(text: str, url: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, url=url)


def _build_cb_button(text: str, callback_data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=callback_data)


# ─── Главное меню ──────────────────────────────────────────────────────

def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _build_cb_button("📱 Арендовать", "rent"),
        _build_cb_button("📋 Мои аренды", "my_rents"),
        width=2,
    )
    builder.row(
        _build_cb_button("💰 Баланс", "balance"),
        _build_cb_button("❓ Помощь", "help"),
        width=2,
    )
    return builder.as_markup()


# ─── Выбор сервиса ─────────────────────────────────────────────────────

def service_selection_kb(services: Optional[list[dict]] = None) -> InlineKeyboardMarkup:
    """Сетка сервисов по 3 в ряд + кнопка 'Другой сервис'."""
    if services is None:
        services = SERVICES

    builder = InlineKeyboardBuilder()

    # По 3 сервиса в ряд
    for i in range(0, len(services), 3):
        row_services = services[i:i + 3]
        buttons = [
            _build_cb_button(
                f"{s['emoji']} {s['name']}",
                f"service:{s['code']}",
            )
            for s in row_services
        ]
        builder.row(*buttons, width=3)

    # Кнопка "Другой сервис"
    builder.row(
        _build_cb_button("🔍 Другой сервис", "other_service"),
        _build_cb_button("🏠 Главная", "main_menu"),
        width=2,
    )

    return builder.as_markup()


# ─── Выбор страны ──────────────────────────────────────────────────────

def country_selection_kb(
    countries: Optional[list[dict]] = None,
    page: int = 0,
) -> InlineKeyboardMarkup:
    """Список стран с флагами, по ITEMS_PER_PAGE на страницу + пагинация."""
    if countries is None:
        countries = COUNTRIES

    total_pages = (len(countries) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    page = max(0, min(page, total_pages - 1))

    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_countries = countries[start:end]

    builder = InlineKeyboardBuilder()

    # Кнопки стран: флаг + название + цена
    for c in page_countries:
        price_str = f"${c['price_activation']:.2f}"
        builder.row(
            _build_cb_button(
                f"{c['flag']} {c['name']} — {price_str}",
                f"country:{c['id']}",
            ),
            width=1,
        )

    # Пагинация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            _build_cb_button("◀️", f"country_page:{page - 1}")
        )
    if page < total_pages - 1:
        nav_buttons.append(
            _build_cb_button("▶️", f"country_page:{page + 1}")
        )

    if nav_buttons:
        # Добавляем индикатор страницы
        page_indicator = f"📄 {page + 1}/{total_pages}"
        builder.row(
            _build_cb_button(page_indicator, "noop"),
            *nav_buttons,
            width=1 + len(nav_buttons),
        )

    # Навигация назад
    builder.row(
        _build_cb_button("🔙 Назад", "back"),
        _build_cb_button("🏠 Главная", "main_menu"),
        width=2,
    )

    return builder.as_markup()


# ─── Выбор типа аренды ─────────────────────────────────────────────────

def rent_type_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _build_cb_button("🎯 Активация (20 мин)", "rent_type:activation"),
        width=1,
    )
    builder.row(
        _build_cb_button("📦 Аренда (от 4 часов)", "rent_type:rent"),
        width=1,
    )
    builder.row(
        _build_cb_button("🔙 Назад", "back"),
        _build_cb_button("🏠 Главная", "main_menu"),
        width=2,
    )
    return builder.as_markup()


# ─── Выбор длительности ────────────────────────────────────────────────

def duration_selection_kb() -> InlineKeyboardMarkup:
    """
    Клавиатура выбора длительности аренды.
    Цены рассчитываются на основе базовой цены за час.
    """
    durations = [
        (4, "⏱ 4 часа"),
        (12, "⏱ 12 часов"),
        (24, "⏱ 24 часа"),
        (72, "⏱ 3 дня"),
        (168, "⏱ 7 дней"),
        (336, "⏱ 14 дней"),
    ]

    builder = InlineKeyboardBuilder()

    # По 2 в ряд
    for i in range(0, len(durations), 2):
        row = durations[i:i + 2]
        buttons = [
            _build_cb_button(label, f"duration:{hours}")
            for hours, label in row
        ]
        builder.row(*buttons, width=2)

    builder.row(
        _build_cb_button("🔙 Назад", "back"),
        _build_cb_button("🏠 Главная", "main_menu"),
        width=2,
    )

    return builder.as_markup()


# ─── Подтверждение ─────────────────────────────────────────────────────

def confirm_kb(price: float) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _build_cb_button(f"✅ Подтвердить ${price:.2f}", "confirm_rent"),
        width=1,
    )
    builder.row(
        _build_cb_button("🔙 Назад", "back"),
        _build_cb_button("🏠 Главная", "main_menu"),
        width=2,
    )
    return builder.as_markup()


# ─── Управление арендой ────────────────────────────────────────────────

def rent_control_kb(rent_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _build_cb_button("📩 SMS", f"get_sms:{rent_id}"),
        _build_cb_button("🔄 Продлить", f"extend_rent:{rent_id}"),
        width=2,
    )
    builder.row(
        _build_cb_button("❌ Отменить", f"cancel_rent:{rent_id}"),
        _build_cb_button("🔙 Назад", "my_rents"),
        width=2,
    )
    builder.row(
        _build_cb_button("🏠 Главная", "main_menu"),
        width=1,
    )
    return builder.as_markup()


# ─── Баланс ────────────────────────────────────────────────────────────

def balance_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _build_cb_button("💳 Пополнить", "topup"),
        _build_cb_button("🔄 Обновить", "balance"),
        width=2,
    )
    builder.row(
        _build_cb_button("🏠 Главная", "main_menu"),
        width=1,
    )
    return builder.as_markup()


# ─── Список моих аренд ─────────────────────────────────────────────────

def my_rents_kb(rents: list[dict]) -> InlineKeyboardMarkup:
    """Клавиатура со списком активных аренд пользователя."""
    builder = InlineKeyboardBuilder()

    for rent in rents:
        emoji = "📱"
        builder.row(
            _build_cb_button(
                f"{emoji} #{rent['id']} {rent['phone']} — {rent['service_name']}",
                f"rent_detail:{rent['id']}",
            ),
            width=1,
        )

    builder.row(
        _build_cb_button("🏠 Главная", "main_menu"),
        width=1,
    )

    return builder.as_markup()


# ─── Простые клавиатуры ────────────────────────────────────────────────

def back_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _build_cb_button("🔙 Назад", "back"),
        width=1,
    )
    return builder.as_markup()


def cancel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _build_cb_button("❌ Отмена", "cancel"),
        width=1,
    )
    return builder.as_markup()


def yes_no_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _build_cb_button("✅ Да", "yes"),
        _build_cb_button("❌ Нет", "no"),
        width=2,
    )
    return builder.as_markup()


def back_main_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _build_cb_button("🏠 Главное меню", "main_menu"),
        width=1,
    )
    return builder.as_markup()


def topup_kb() -> InlineKeyboardMarkup:
    """Клавиатура с быстрыми суммами для пополнения."""
    builder = InlineKeyboardBuilder()
    builder.row(
        _build_cb_button("💵 $5", "topup_amount:5"),
        _build_cb_button("💵 $10", "topup_amount:10"),
        _build_cb_button("💵 $25", "topup_amount:25"),
        _build_cb_button("💵 $50", "topup_amount:50"),
        width=4,
    )
    builder.row(
        _build_cb_button("❌ Отмена", "main_menu"),
        width=1,
    )
    return builder.as_markup()


def extend_duration_kb(current_rent_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для продления аренды с выбором срока."""
    builder = InlineKeyboardBuilder()
    builder.row(
        _build_cb_button("⏱ +4 часа", f"extend_confirm:{current_rent_id}:4"),
        _build_cb_button("⏱ +12 часов", f"extend_confirm:{current_rent_id}:12"),
        _build_cb_button("⏱ +24 часа", f"extend_confirm:{current_rent_id}:24"),
        width=2,
    )
    builder.row(
        _build_cb_button("⏱ +3 дня", f"extend_confirm:{current_rent_id}:72"),
        _build_cb_button("⏱ +7 дней", f"extend_confirm:{current_rent_id}:168"),
        width=2,
    )
    builder.row(
        _build_cb_button("🔙 Назад", f"rent_detail:{current_rent_id}"),
        _build_cb_button("🏠 Главная", "main_menu"),
        width=2,
    )
    return builder.as_markup()
