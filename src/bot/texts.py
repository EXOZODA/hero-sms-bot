"""
Премиальные HTML-тексты для всех сообщений бота.
Все строки возвращаются готовыми к отправке (parse_mode=HTML).
"""

from typing import Optional


class Texts:
    """Сборник всех текстовых сообщений бота."""

    SEPARATOR = "━━━━━━━━━━━━━━━━━━"
    SEPARATOR_THIN = "─" * 24

    # ─── Приветствие / Старт ─────────────────────────────────────────

    @staticmethod
    def welcome_new() -> str:
        return (
            f"🌟 <b>Добро пожаловать в HeroSMS</b> 🌟\n\n"
            f"Ваш премиум-доступ к виртуальным номерам\n"
            f"для регистрации в любых сервисах.\n\n"
            f"{Texts.SEPARATOR}\n"
            f"📱 <b>500+ сервисов</b>\n"
            f"🌍 <b>180+ стран мира</b>\n"
            f"⚡ <b>Мгновенная аренда</b>\n"
            f"{Texts.SEPARATOR}\n\n"
            f"Выберите действие 👇"
        )

    @staticmethod
    def welcome_back() -> str:
        return (
            f"🌟 <b>С возвращением в HeroSMS!</b> 🌟\n\n"
            f"Рады видеть вас снова. Ваши активные аренды\n"
            f"продолжают работать в штатном режиме.\n\n"
            f"Выберите действие 👇"
        )

    @staticmethod
    def main_menu(username: str, balance: float, active_count: int) -> str:
        return (
            f"🌟 <b>HeroSMS — премиум-панель</b>\n\n"
            f"👤 <b>Профиль:</b> @{username}\n"
            f"💰 <b>Баланс:</b> ${balance:.2f}\n"
            f"📋 <b>Активных аренд:</b> {active_count}\n\n"
            f"{Texts.SEPARATOR}\n"
            f"Выберите действие 👇"
        )

    # ─── Сервисы ──────────────────────────────────────────────────────

    @staticmethod
    def select_service() -> str:
        return (
            f"🔧 <b>Выберите сервис</b>\n\n"
            f"Ниже представлены самые популярные сервисы.\n"
            f"Выберите нужный для получения виртуального номера.\n\n"
            f"{Texts.SEPARATOR}"
        )

    @staticmethod
    def other_service() -> str:
        return (
            f"🔍 <b>Другие сервисы</b>\n\n"
            f"В настоящее время доступен поиск по каталогу.\n"
            f"Напишите название сервиса вручную или выберите\n"
            f"из списка популярных выше.\n\n"
            f"{Texts.SEPARATOR}"
        )

    # ─── Страны ───────────────────────────────────────────────────────

    @staticmethod
    def select_country(service_name: str) -> str:
        return (
            f"🌍 <b>Выберите страну</b>\n\n"
            f"Доступные страны для сервиса <b>{service_name}</b>:\n\n"
            f"Отображаются цены для активации / за час аренды 👇"
        )

    @staticmethod
    def country_item(flag: str, name: str, price_act: float, price_hour: float) -> str:
        return f"{flag} <b>{name}</b>  │  🎯 ${price_act:.2f} / 📦 ${price_hour:.2f}/ч"

    # ─── Тип аренды ───────────────────────────────────────────────────

    @staticmethod
    def select_rent_type(service_name: str, country_flag: str, country_name: str) -> str:
        return (
            f"📋 <b>Выберите тип аренды</b>\n\n"
            f"🔧 <b>Сервис:</b> {service_name}\n"
            f"🌍 <b>Страна:</b> {country_flag} {country_name}\n\n"
            f"{Texts.SEPARATOR}\n"
            f"🎯 <b>Активация</b> — для получения кода подтверждения\n"
            f"⏱ Длительность: ~20 минут\n"
            f"💰 Цена фиксированная\n\n"
            f"📦 <b>Аренда</b> — полноценный номер на длительный срок\n"
            f"⏱ От 4 часов до 14 дней\n"
            f"💰 Оплата за час\n"
            f"{Texts.SEPARATOR}\n\n"
            f"Выберите тип 👇"
        )

    @staticmethod
    def rent_type_activation() -> str:
        return "🎯 Активация"

    @staticmethod
    def rent_type_rent() -> str:
        return "📦 Аренда"

    # ─── Длительность ─────────────────────────────────────────────────

    @staticmethod
    def select_duration(service_name: str, country_flag: str, country_name: str, price_per_hour: float) -> str:
        return (
            f"⏱ <b>Выберите длительность аренды</b>\n\n"
            f"🔧 <b>Сервис:</b> {service_name}\n"
            f"🌍 <b>Страна:</b> {country_flag} {country_name}\n"
            f"💰 <b>Цена за час:</b> ${price_per_hour:.2f}\n\n"
            f"{Texts.SEPARATOR}\n"
            f"Чем дольше срок — тем выгоднее цена! 👇"
        )

    @staticmethod
    def duration_option(hours: int, total_price: float) -> str:
        if hours < 24:
            label = f"{hours} ч"
        elif hours < 24 * 7:
            label = f"{hours // 24} д"
        else:
            label = f"{hours // 24} д"
        return f"⏱ {label} — ${total_price:.2f}"

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
        type_label = "🎯 Активация" if rent_type == "activation" else "📦 Аренда"
        duration_line = ""
        if rent_type == "rent" and duration:
            if duration < 24:
                dur_str = f"{duration} ч"
            else:
                dur_str = f"{duration // 24} д"
            duration_line = f"⏱ <b>Длительность:</b> {dur_str}\n"

        return (
            f"📋 <b>Подтверждение заказа</b>\n\n"
            f"{Texts.SEPARATOR}\n"
            f"🔧 <b>Сервис:</b> {service_name}\n"
            f"🌍 <b>Страна:</b> {country_flag} {country_name}\n"
            f"📦 <b>Тип:</b> {type_label}\n"
            f"{duration_line}"
            f"{Texts.SEPARATOR}\n\n"
            f"💰 <b>Итого к оплате:</b> ${price:.2f}\n\n"
            f"Подтвердите заказ 👇"
        )

    @staticmethod
    def rent_success(rent_id: int, phone: str) -> str:
        return (
            f"✅ <b>Аренда успешно начата!</b> 🎉\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📱 <b>Номер:</b> <code>{phone}</code>\n"
            f"🆔 <b>ID аренды:</b> {rent_id}\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"Все SMS будут приходить автоматически.\n"
            f"Используйте кнопки управления ниже 👇"
        )

    @staticmethod
    def rent_cancelled(rent_id: int) -> str:
        return (
            f"❌ <b>Аренда #{rent_id} отменена</b>\n\n"
            f"Номер больше неактивен. Средства за\n"
            f"оставшееся время возвращены на баланс.\n\n"
            f"{Texts.SEPARATOR}"
        )

    @staticmethod
    def rent_extended(rent_id: int, new_expiry: str) -> str:
        return (
            f"🔄 <b>Аренда #{rent_id} продлена</b> ✅\n\n"
            f"Новый срок действия: <b>{new_expiry}</b>\n\n"
            f"{Texts.SEPARATOR}"
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
        sms_list: list[str],
    ) -> str:
        type_emoji = "🎯" if rent_type == "activation" else "📦"
        type_label = "Активация" if rent_type == "activation" else "Аренда"

        sms_block = ""
        if sms_list:
            sms_lines = "\n".join(f"  📩 <code>{s}</code>" for s in sms_list)
            sms_block = f"📩 <b>SMS ({len(sms_list)}):</b>\n{sms_lines}"
        else:
            sms_block = "📩 <b>SMS:</b> ⏳ ожидание..."

        return (
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📱 <b>{phone}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 <b>ID:</b> {rent_id}\n"
            f"🔧 <b>Сервис:</b> {service_name}\n"
            f"🌍 <b>Страна:</b> {country_flag} {country_name}\n"
            f"{type_emoji} <b>Тип:</b> {type_label}\n"
            f"⏱ <b>Осталось:</b> {time_left}\n"
            f"💰 <b>Цена:</b> ${price:.2f}\n\n"
            f"{sms_block}\n\n"
            f"━━━━━━━━━━━━━━━━━━"
        )

    # ─── Список аренд ─────────────────────────────────────────────────

    @staticmethod
    def my_rents_empty() -> str:
        return (
            f"📋 <b>Мои аренды</b>\n\n"
            f"У вас пока нет активных аренд.\n"
            f"Нажмите «📱 Арендовать» в главном меню,\n"
            f"чтобы получить виртуальный номер.\n\n"
            f"{Texts.SEPARATOR}"
        )

    @staticmethod
    def my_rents_list(rents_info: str) -> str:
        return (
            f"📋 <b>Мои аренды</b>\n\n"
            f"{rents_info}\n"
            f"{Texts.SEPARATOR}\n"
            f"Выберите аренду для управления 👇"
        )

    @staticmethod
    def rent_list_item(emoji: str, rent_id: int, phone: str, service_name: str) -> str:
        return f"{emoji} <b>#{rent_id}</b> {phone} — {service_name}"

    # ─── Баланс ───────────────────────────────────────────────────────

    @staticmethod
    def balance_show(balance: float, total_spent: float) -> str:
        return (
            f"💰 <b>Ваш баланс</b>\n\n"
            f"{Texts.SEPARATOR}\n"
            f"💎 Текущий баланс: <b>${balance:.2f}</b>\n"
            f"📊 Всего потрачено: <b>${total_spent:.2f}\n"
            f"{Texts.SEPARATOR}\n\n"
            f"Выберите действие 👇"
        )

    @staticmethod
    def topup_prompt() -> str:
        return (
            f"💳 <b>Пополнение баланса</b>\n\n"
            f"Введите сумму пополнения в долларах США.\n\n"
            f"{Texts.SEPARATOR}\n"
            f"💰 <b>Минимум:</b> $1.00\n"
            f"💰 <b>Максимум:</b> $500.00\n"
            f"{Texts.SEPARATOR}\n\n"
            f"Пример: <code>25.50</code>"
        )

    @staticmethod
    def topup_success(amount: float, new_balance: float) -> str:
        return (
            f"✅ <b>Баланс пополнен!</b>\n\n"
            f"💰 Пополнено: <b>+${amount:.2f}</b>\n"
            f"💎 Новый баланс: <b>${new_balance:.2f}</b>\n\n"
            f"{Texts.SEPARATOR}"
        )

    @staticmethod
    def topup_invalid_amount() -> str:
        return (
            f"❌ <b>Неверная сумма</b>\n\n"
            f"Пожалуйста, введите число от $1.00 до $500.00.\n"
            f"Используйте точку как разделитель (например, 25.50).\n\n"
            f"{Texts.SEPARATOR}\n"
            f"Попробуйте снова 👇"
        )

    # ─── SMS ──────────────────────────────────────────────────────────

    @staticmethod
    def sms_received(sms_list: list[str]) -> str:
        if not sms_list:
            return (
                f"📩 <b>SMS-сообщения</b>\n\n"
                f"⏳ Пока нет новых сообщений.\n"
                f"Ожидаем поступление SMS на ваш номер...\n\n"
                f"{Texts.SEPARATOR}\n"
                f"Попробуйте обновить позже 👇"
            )

        lines = "\n\n".join(
            f"📩 <b>SMS #{i + 1}</b>\n<code>{sms}</code>"
            for i, sms in enumerate(sms_list)
        )
        return (
            f"📩 <b>SMS-сообщения</b>\n\n"
            f"{lines}\n\n"
            f"{Texts.SEPARATOR}"
        )

    # ─── Помощь ───────────────────────────────────────────────────────

    @staticmethod
    def help_text() -> str:
        return (
            f"❓ <b>Помощь по HeroSMS</b>\n\n"
            f"{Texts.SEPARATOR}\n\n"
            f"📱 <b>Что это?</b>\n"
            f"HeroSMS предоставляет виртуальные номера\n"
            f"для регистрации в любых сервисах мира.\n\n"
            f"🎯 <b>Активация</b>\n"
            f"Номер на 20 минут для получения кода.\n"
            f"Идеально для разовых регистраций.\n\n"
            f"📦 <b>Аренда</b>\n"
            f"Номер на срок от 4 часов до 14 дней.\n"
            f"Для длительного использования.\n\n"
            f"💳 <b>Оплата</b>\n"
            f"Пополняйте баланс и оплачивайте услуги.\n"
            f"Минимальная сумма пополнения — $1.00.\n\n"
            f"{Texts.SEPARATOR}\n\n"
            f"🆘 <b>Поддержка:</b> @HeroSMS_support\n\n"
            f"Выберите действие 👇"
        )

    # ─── Ошибки ───────────────────────────────────────────────────────

    @staticmethod
    def error_message(error_text: str = "Произошла неизвестная ошибка.") -> str:
        return (
            f"❌ <b>Ошибка</b>\n\n"
            f"{error_text}\n\n"
            f"{Texts.SEPARATOR}\n"
            f"⚠️ Попробуйте позже или обратитесь в поддержку."
        )

    @staticmethod
    def rate_limit() -> str:
        return (
            f"⏳ <b>Слишком часто</b>\n\n"
            f"Пожалуйста, подождите немного перед\n"
            f"следующим запросом.\n\n"
            f"{Texts.SEPARATOR}"
        )

    @staticmethod
    def service_unavailable() -> str:
        return (
            f"🔧 <b>Сервис временно недоступен</b>\n\n"
            f"Попробуйте выбрать другой сервис\n"
            f"или повторите попытку позже.\n\n"
            f"{Texts.SEPARATOR}"
        )

    @staticmethod
    def rent_not_found() -> str:
        return (
            f"❌ <b>Аренда не найдена</b>\n\n"
            f"Возможно, она уже завершена или\n"
            f"была отменена.\n\n"
            f"{Texts.SEPARATOR}"
        )

    @staticmethod
    def insufficient_balance(balance: float, required: float) -> str:
        return (
            f"❌ <b>Недостаточно средств</b>\n\n"
            f"💎 Ваш баланс: <b>${balance:.2f}</b>\n"
            f"💰 Требуется: <b>${required:.2f}</b>\n\n"
            f"Пополните баланс в главном меню.\n"
            f"{Texts.SEPARATOR}"
        )

    @staticmethod
    def private_chat_only() -> str:
        return (
            f"🚫 <b>Этот бот работает только в личных сообщениях.</b>\n"
            f"Перейдите в @HeroSMS_bot в личном чате."
        )
