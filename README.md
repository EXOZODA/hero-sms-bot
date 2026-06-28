# 🤖 HeroSMS Rent Bot

Премиальный Telegram бот для аренды виртуальных номеров через [HeroSMS API](https://hero-sms.com).

## ✨ Возможности

- 🌍 **180+ стран** для аренды номеров
- 🔧 **500+ сервисов** (Telegram, WhatsApp, Instagram, Google, Facebook и др.)
- 🎯 **Активации** — номера на 20 минут для одноразовых кодов
- 📦 **Аренда** — номера от 4 часов до 14 дней
- 💰 **Управление балансом** — пополнение, история трат
- 📩 **Получение SMS** в реальном времени
- 🔄 **Продление и отмена** аренды

## 🛠️ Технологии

- **Python 3.12** + **aiogram 3.x** (Telegram Bot API)
- **FastAPI** + **Uvicorn** (Webhook сервер)
- **SQLite** + **aiosqlite** (база данных)
- **httpx** (асинхронный HTTP-клиент)
- **Render.com** (хостинг, бесплатный тариф)

## 🚀 Быстрый старт

### 1. Клонировать репозиторий
```bash
git clone https://github.com/EXOZODA/hero-sms-bot.git
cd hero-sms-bot
```

### 2. Установить зависимости
```bash
pip install -r requirements.txt
```

### 3. Настроить окружение
Создать файл `.env`:
```env
BOT_TOKEN=ваш_токен_от_BotFather
HERO_SMS_API_KEY=ваш_ключ_hero_sms
WEBHOOK_URL=https://ваш-бот.onrender.com
WEBHOOK_SECRET_TOKEN=случайная_строка
```

### 4. Запустить локально (polling)
```bash
python main.py --polling
```

### 5. Деплой на Render.com
- Создать **Web Service** из GitHub репозитория
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python main.py`
- Добавить переменные окружения из `.env`

## 📁 Структура проекта

```
hero-sms-bot/
├── main.py              # Точка входа (FastAPI + webhook)
├── requirements.txt     # Зависимости
├── runtime.txt          # Версия Python
├── .env.example         # Шаблон конфига
│
└── src/
    ├── config.py                   # Конфигурация
    ├── bot/                        # Telegram Bot
    │   ├── texts.py                #     Шаблоны сообщений
    │   ├── keyboards.py            #     Inline-клавиатуры
    │   ├── handlers.py             #     Обработчики
    │   ├── states.py               #     FSM состояния
    │   ├── middlewares.py          #     Middleware
    │   └── filters.py              #     Фильтры
    ├── api/
    │   └── hero_client.py          # HeroSMS API клиент
    ├── db/
    │   ├── models.py               # Модели данных
    │   └── repository.py           # CRUD операции
    └── services/
        └── rent.py                 # Бизнес-логика
```

## 🔒 Безопасность

- Все секреты хранятся в переменных окружения
- API ключ передаётся только на серверы Render (EU)
- Webhook защищён secret_token
- SQL-инъекции предотвращены (параметризованные запросы)
- Rate limiting: не более 1 запроса/сек на пользователя

## 📄 Лицензия

MIT
