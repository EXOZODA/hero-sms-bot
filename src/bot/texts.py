"""
Премиальные HTML-тексты с кастомными черно-белыми иконками.

Все иконки — монохромные Unicode символы для стильного минимализма.
Цветные флаги стран сохранены для удобства восприятия.
"""

from typing import Optional

from src.bot.icons import (
    ARROW_R, BULLET, CHECK, CLOCK, COIN, CROSS, CROWN, DIAMOND,
    GLOBE, GRID, HELP, HOME, LIST, MAIL, MENU, PHONE, PLUS,
    REFRESH, SEARCH, SEP_DOTS, SEP_THICK, SEP_THIN, STAR,
    STATUS_ACTIVE, STATUS_INACTIVE, STATUS_WAITING, TOOL, WARN,
    get_service_icon,
)


class Texts:
    """Сборник всех текстовых сообщений бота."""

    SEPARATOR = SEP_THICK

    # ─── Приветствие / Старт ─────────────────────────────────────────

    @staticmethod
    def welcome_new() -> str:
        return (
            f"{CROWN} <b>HeroSMS — Премиум номера</b>\n\n"
            f"Виртуальные номера для регистрации\n"
            f"в любых сервисах мира.\n\n"
            f"{SEP_THICK}\n"
            f"{PHONE} <b>500+ сервисов</b>\n"
            f"{GLOBE} <b>180+ стран</b>\n"
            f"{STAR} <b>Мгновенная аренда</b>\n"
            f"{SEP_THICK}\n\n"
            f"Выберите действие {ARROW_R}"
        )

    @staticmethod
    def welcome_back() -> str:
        return (
            f"{CROWN} <b>С возвращением в HeroSMS</b>\n\n"
            f"Ваши активные аренды продолжают\n"
            f"работать в штатном режиме.\n\n"
            f"Выберите действие {ARROW_R}"
        )

    @staticmethod
    def main_menu(username: str, balance: float, active_count: int) -> str:
        return (
            f"{CROWN} <b>HeroSMS — Панель</b>\n\n"
            f"{BULLET} <b>Профиль:</b> @{username}\n"
            f"{COIN} <b>Баланс:</b> ${balance:.2f}\n"
            f"{LIST} <b>Активных аренд:</b> {active_count}\n\n"
            f"{SEP_THIN}\n"
            f"Выберите действие {ARROW_R}"
        )

    # ─── Сервисы ──────────────────────────────────────────────────────

    @staticmethod
    def select_service() -> str:
        return (
            f"{TOOL} <b>Выберите сервис</b>\n\n"
            f"Популярные сервисы для получения номера.\n"
            f"{SEP_THIN}"
        )

    @staticmethod
    def other_service() -> str:
        return (
            f"{SEARCH} <b>Другие сервисы</b>\n\n"
            f"Напишите название сервиса вручную\n"
            f"или выберите из списка выше.\n"
            f"{SEP_THIN}"
        )

    # ─── Страны ───────────────────────────────────────────────────────

    @staticmethod
    def select_country(service_name: str) -> str:
        return (
            f"{GLOBE} <b>Выберите страну</b>\n\n"
            f"{TOOL} <b>Сервис:</b> {service_name}\n\n"
            f"Показаны цены за активацию {ARROW_R}"
        )

    # ─── Тип аренды ───────────────────────────────────────────────────

    @staticmethod
    def select_rent_type(service_name: str, country_flag: str, country_name: str) -> str:
        return (
            f"{TOOL} <b>Тип аренды</b>\n\n"
            f"{TOOL} <b>Сервис:</b> {service_name}\n"
            f"{GLOBE} <b>Страна:</b> {country_flag} {country_name}\n\n"
            f"{SEP_THIN}\n"
            f"{PHONE} <b>Активация</b> — 20 мин, один код\n"
            f"{STAR} <b>Аренда</b> — от 4 часов до 14 дней\n"
            f"{SEP_THIN}\n\n"
            f"Выберите тип {ARROW_R}"
        )

    # ─── Длительность ─────────────────────────────────────────────────

    @staticmethod
    def select_duration(
        service_name: str,
        country_flag: str,
        country_name: str,
        price_per_hour: float,
    ) -> str:
        return (
            f"{CLOCK} <b>Длительность аренды</b>\n\n"
            f"{TOOL} <b>Сервис:</b> {service_name}\n"
            f"{GLOBE} <b>Страна:</b> {country_flag} {country_name}\n"
            f"{COIN} <b>Цена/час:</b> ${price_per_hour:.2f}\n\n"
            f"{SEP_THIN}\n"
            f"Чем дольше срок — тем выгоднее {ARROW_R}"
        )

    # ─── Подтверждение ────────────────────────────────────────────────

    @staticmethod
    def confirm_rent(
        service_name: str,
        country_flag: str,
        country_name: str,
        rent_type: str,
        duration: Optional[int],
        price: float,
    ) -> str:
        type_label = f"{PHONE} Активация" if rent_type == "activation" else f"{STAR} Аренда"
        duration_line = ""
        if rent_type == "rent" and duration:
            if duration < 24:
                dur_str = f"{duration} ч"
            else:
                dur_str = f"{duration // 24} д"
            duration_line = f"{CLOCK} <b>Длительность:</b> {dur_str}\n"

        return (
            f"{CHECK} <b>Подтверждение заказа</b>\n\n"
            f"{SEP_THICK}\n"
            f"{TOOL} <b>Сервис:</b> {service_name}\n"
            f"{GLOBE} <b>Страна:</b> {country_flag} {country_name}\n"
            f"{type_label}\n"
            f"{duration_line}"
            f"{SEP_THICK}\n\n"
            f"{COIN} <b>Итого:</b> ${price:.2f}\n\n"
            f"Подтвердите заказ {ARROW_R}"
        )

    @staticmethod
    def rent_success(rent_id: int, phone: str) -> str:
        return (
            f"{CHECK} <b>Аренда начата!</b>\n\n"
            f"{SEP_THICK}\n"
            f"{PHONE} <b>Номер:</b> <code>{phone}</code>\n"
            f"{BULLET} <b>ID:</b> {rent_id}\n"
            f"{SEP_THICK}\n\n"
            f"{CLOCK} Ожидайте SMS на номер."
        )

    # ─── Карточка аренды ──────────────────────────────────────────────

    @staticmethod
    def rent_card(
        rent_id: int,
        phone: str,
        service_name: str,
        country_flag: str,
        country_name: str,
        rent_type: str,
        time_left: str,
        price: float,
        sms_list: Optional[list[str]] = None,
    ) -> str:
        if sms_list is None:
            sms_list = []

        type_icon = PHONE if rent_type == "activation" else STAR
        type_label = "Активация" if rent_type == "activation" else "Аренда"

        # Форматируем SMS
        sms_block = ""
        if sms_list:
            items = "\n".join(f"  {BULLET} <code>{s}</code>" for s in sms_list)
            sms_block = f"{MAIL} <b>SMS:</b>\n{items}"
        else:
            sms_block = f"{MAIL} <b>SMS:</b> {CLOCK} ожидание..."

        return (
            f"{SEP_THICK}\n"
            f"{PHONE} <b>{phone}</b>\n"
            f"{SEP_THICK}\n\n"
            f"{BULLET} <b>ID:</b> {rent_id}\n"
            f"{TOOL} <b>Сервис:</b> {service_name}\n"
            f"{type_icon} <b>Тип:</b> {type_label}\n"
            f"{CLOCK} <b>Осталось:</b> {time_left}\n"
            f"{COIN} <b>Цена:</b> ${price:.2f}\n\n"
            f"{sms_block}\n\n"
            f"{SEP_THICK}"
        )

    # ─── Список аренд ─────────────────────────────────────────────────

    @staticmethod
    def my_rents_empty() -> str:
        return (
            f"{LIST} <b>Мои аренды</b>\n\n"
            f"У вас пока нет активных аренд.\n\n"
            f"{SEP_THIN}"
        )

    @staticmethod
    def my_rents_list(rents_info: str) -> str:
        return (
            f"{LIST} <b>Мои аренды</b>\n\n"
            f"{rents_info}\n"
            f"{SEP_THIN}\n"
            f"Выберите аренду {ARROW_R}"
        )

    @staticmethod
    def rent_list_item(emoji: str, rent_id: int, phone: str, service_name: str) -> str:
        return f"{emoji} <b>#{rent_id}</b> {phone} — {service_name}"

    # ─── Баланс ───────────────────────────────────────────────────────

    @staticmethod
    def balance_show(balance: float, total_spent: float) -> str:
        return (
            f"{COIN} <b>Баланс</b>\n\n"
            f"{SEP_THICK}\n"
            f"{DIAMOND} Текущий: <b>${balance:.2f}</b>\n"
            f"{LIST} Потрачено: <b>${total_spent:.2f}</b>\n"
            f"{SEP_THICK}\n\n"
            f"Выберите действие {ARROW_R}"
        )

    @staticmethod
    def topup_prompt() -> str:
        return (
            f"{PLUS} <b>Пополнение баланса</b>\n\n"
            f"Введите сумму в долларах США.\n\n"
            f"{SEP_THIN}\n"
            f"{COIN} <b>Мин:</b> $1.00\n"
            f"{COIN} <b>Макс:</b> $500.00\n"
            f"{SEP_THIN}\n\n"
            f"Пример: <code>25.50</code>"
        )

    @staticmethod
    def topup_success(amount: float, new_balance: float) -> str:
        return (
            f"{CHECK} <b>Баланс пополнен!</b>\n\n"
            f"{PLUS} Пополнено: <b>+${amount:.2f}</b>\n"
            f"{COIN} Баланс: <b>${new_balance:.2f}</b>\n\n"
            f"{SEP_THIN}"
        )

    @staticmethod
    def topup_invalid_amount() -> str:
        return (
            f"{CROSS} <b>Неверная сумма</b>\n\n"
            f"Введите число от $1.00 до $500.00.\n"
            f"Используйте точку (например, 25.50).\n\n"
            f"{SEP_THIN}\n"
            f"Попробуйте снова {ARROW_R}"
        )

    # ─── SMS ──────────────────────────────────────────────────────────

    @staticmethod
    def sms_received(sms_list: list[str]) -> str:
        if not sms_list:
            return (
                f"{MAIL} <b>SMS-сообщения</b>\n\n"
                f"{CLOCK} Пока нет новых сообщений.\n"
                f"Ожидаем подтверждение...\n\n"
                f"{SEP_THIN}"
            )

        lines = "\n\n".join(
            f"{MAIL} <b>SMS #{i + 1}</b>\n<code>{sms}</code>"
            for i, sms in enumerate(sms_list)
        )
        return (
            f"{MAIL} <b>SMS-сообщения</b>\n\n"
            f"{lines}\n\n"
            f"{SEP_THIN}"
        )

    # ─── Помощь ───────────────────────────────────────────────────────

    @staticmethod
    def help_text() -> str:
        return (
            f"{HELP} <b>Помощь по HeroSMS</b>\n\n"
            f"{SEP_THICK}\n\n"
            f"{PHONE} <b>Что это?</b>\n"
            f"Виртуальные номера для регистрации\n"
            f"в любых сервисах мира.\n\n"
            f"{STAR} <b>Активация</b>\n"
            f"Номер на 20 минут для одного кода.\n\n"
            f"{STAR} <b>Аренда</b>\n"
            f"Номер от 4 часов до 14 дней.\n\n"
            f"{COIN} <b>Оплата</b>\n"
            f"Пополняйте баланс. Мин. $1.00.\n\n"
            f"{SEP_THICK}\n\n"
            f"{HOME} Используйте меню для навигации {ARROW_R}"
        )

    # ─── Ошибки ───────────────────────────────────────────────────────

    @staticmethod
    def error_message(error_text: str = "Произошла неизвестная ошибка.") -> str:
        return (
            f"{CROSS} <b>Ошибка</b>\n\n"
            f"{error_text}\n\n"
            f"{SEP_THIN}\n"
            f"{WARN} Попробуйте позже."
        )

    @staticmethod
    def rate_limit() -> str:
        return (
            f"{CLOCK} <b>Слишком часто</b>\n\n"
            f"Подождите немного перед следующим запросом.\n\n"
            f"{SEP_THIN}"
        )

    @staticmethod
    def service_unavailable() -> str:
        return (
            f"{TOOL} <b>Сервис недоступен</b>\n\n"
            f"Попробуйте другой сервис\n"
            f"или повторите попытку позже.\n\n"
            f"{SEP_THIN}"
        )

    @staticmethod
    def rent_not_found() -> str:
        return (
            f"{CROSS} <b>Аренда не найдена</b>\n\n"
            f"Возможно, она уже завершена.\n\n"
            f"{SEP_THIN}"
        )

    @staticmethod
    def insufficient_balance(balance: float, required: float) -> str:
        return (
            f"{CROSS} <b>Недостаточно средств</b>\n\n"
            f"{COIN} Ваш баланс: <b>${balance:.2f}</b>\n"
            f"{COIN} Требуется: <b>${required:.2f}</b>\n\n"
            f"Пополните баланс в меню.\n"
            f"{SEP_THIN}"
        )

    @staticmethod
    def private_chat_only() -> str:
        return (
            f"{CROSS} <b>Только личные сообщения</b>\n"
            f"Напишите боту в личный чат."
        )
