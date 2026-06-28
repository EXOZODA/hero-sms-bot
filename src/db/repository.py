"""
Репозиторий для работы с БД.

Все операции асинхронные. Использует aiosqlite.
Передавайте соединение через параметр db: aiosqlite.Connection.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Sequence

import aiosqlite

from src.db.models import Rent, SMSMessage, Transaction, User

logger = logging.getLogger(__name__)

# ─── Инициализация БД ──────────────────────────────────────────────────


async def create_tables(db_path: str | Path) -> None:
    """Создаёт таблицы при первом запуске."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row

        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                balance REAL NOT NULL DEFAULT 0.0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS rents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                phone TEXT NOT NULL,
                service TEXT NOT NULL,
                service_name TEXT,
                country TEXT NOT NULL,
                country_id INTEGER NOT NULL,
                rent_type TEXT NOT NULL DEFAULT 'activation',
                duration_hours INTEGER,
                status TEXT NOT NULL DEFAULT 'active',
                hero_activation_id INTEGER,
                hero_rent_id INTEGER,
                price REAL NOT NULL DEFAULT 0.0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                expires_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS sms_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rent_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                code TEXT,
                received_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (rent_id) REFERENCES rents(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_rents_user_id ON rents(user_id);
            CREATE INDEX IF NOT EXISTS idx_rents_status ON rents(status);
            CREATE INDEX IF NOT EXISTS idx_sms_rent_id ON sms_messages(rent_id);
            CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
        """)

        await db.commit()
        logger.info("Database tables created successfully")


# ─── User ──────────────────────────────────────────────────────────────


async def get_user_by_telegram_id(
    db: aiosqlite.Connection,
    telegram_id: int,
) -> Optional[User]:
    """Получить пользователя по telegram_id."""
    cursor = await db.execute(
        "SELECT id, telegram_id, username, balance, created_at FROM users WHERE telegram_id = ?",
        (telegram_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        return None
    return User(
        id=row[0], telegram_id=row[1], username=row[2],
        balance=row[3], created_at=datetime.fromisoformat(row[4]) if row[4] else None,
    )


async def create_user(
    db: aiosqlite.Connection,
    telegram_id: int,
    username: Optional[str] = None,
) -> User:
    """Создать нового пользователя."""
    now = datetime.utcnow().isoformat()
    cursor = await db.execute(
        "INSERT INTO users (telegram_id, username, created_at) VALUES (?, ?, ?)",
        (telegram_id, username, now),
    )
    await db.commit()
    return User(
        id=cursor.lastrowid,
        telegram_id=telegram_id,
        username=username,
        balance=0.0,
        created_at=datetime.fromisoformat(now),
    )


async def get_or_create_user(
    db: aiosqlite.Connection,
    telegram_id: int,
    username: Optional[str] = None,
) -> User:
    """Получить или создать пользователя."""
    user = await get_user_by_telegram_id(db, telegram_id)
    if user is None:
        user = await create_user(db, telegram_id, username)
        logger.info(f"Created new user: telegram_id={telegram_id}, username={username}")
    return user


async def update_user_balance(
    db: aiosqlite.Connection,
    telegram_id: int,
    new_balance: float,
) -> None:
    """Обновить баланс пользователя."""
    await db.execute(
        "UPDATE users SET balance = ? WHERE telegram_id = ?",
        (new_balance, telegram_id),
    )
    await db.commit()


async def add_user_balance(
    db: aiosqlite.Connection,
    telegram_id: int,
    amount: float,
) -> float:
    """Добавить сумму к балансу пользователя. Возвращает новый баланс."""
    cursor = await db.execute(
        "UPDATE users SET balance = balance + ? WHERE telegram_id = ? RETURNING balance",
        (amount, telegram_id),
    )
    row = await cursor.fetchone()
    await db.commit()
    return row[0] if row else 0.0


async def deduct_user_balance(
    db: aiosqlite.Connection,
    telegram_id: int,
    amount: float,
) -> float:
    """Списать сумму с баланса. Возвращает новый баланс."""
    cursor = await db.execute(
        "UPDATE users SET balance = balance - ? WHERE telegram_id = ? AND balance >= ? RETURNING balance",
        (amount, telegram_id, amount),
    )
    row = await cursor.fetchone()
    await db.commit()
    if row is None:
        raise ValueError("Insufficient balance")
    return row[0]


async def get_total_spent(
    db: aiosqlite.Connection,
    telegram_id: int,
) -> float:
    """Получить общую сумму трат пользователя."""
    cursor = await db.execute(
        "SELECT COALESCE(SUM(ABS(amount)), 0) FROM transactions "
        "WHERE user_id = (SELECT id FROM users WHERE telegram_id = ?) AND type = 'spend'",
        (telegram_id,),
    )
    row = await cursor.fetchone()
    return row[0] if row else 0.0


# ─── Rent ──────────────────────────────────────────────────────────────


async def create_rent(db: aiosqlite.Connection, rent: Rent) -> Rent:
    """Создать новую запись аренды."""
    now = datetime.utcnow().isoformat()
    expires = rent.expires_at.isoformat() if rent.expires_at else None

    cursor = await db.execute(
        """INSERT INTO rents
           (user_id, phone, service, service_name, country, country_id,
            rent_type, duration_hours, status, hero_activation_id,
            hero_rent_id, price, created_at, expires_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            rent.user_id, rent.phone, rent.service, rent.service_name,
            rent.country, rent.country_id, rent.rent_type, rent.duration_hours,
            rent.status, rent.hero_activation_id, rent.hero_rent_id,
            rent.price, now, expires,
        ),
    )
    await db.commit()
    rent.id = cursor.lastrowid
    rent.created_at = datetime.fromisoformat(now)
    return rent


async def get_rent_by_id(db: aiosqlite.Connection, rent_id: int) -> Optional[Rent]:
    """Получить аренду по ID."""
    cursor = await db.execute("SELECT * FROM rents WHERE id = ?", (rent_id,))
    row = await cursor.fetchone()
    if row is None:
        return None
    return _row_to_rent(row)


async def get_active_rents_by_user_id(
    db: aiosqlite.Connection,
    user_id: int,
) -> Sequence[Rent]:
    """Получить активные аренды пользователя."""
    cursor = await db.execute(
        "SELECT * FROM rents WHERE user_id = ? AND status IN ('active', 'waiting_sms') ORDER BY created_at DESC",
        (user_id,),
    )
    rows = await cursor.fetchall()
    return [_row_to_rent(r) for r in rows]


async def get_all_active_rents(db: aiosqlite.Connection) -> Sequence[Rent]:
    """Получить все активные аренды (для фоновых задач)."""
    cursor = await db.execute(
        "SELECT * FROM rents WHERE status IN ('active', 'waiting_sms') ORDER BY created_at DESC",
    )
    rows = await cursor.fetchall()
    return [_row_to_rent(r) for r in rows]


async def update_rent_status(
    db: aiosqlite.Connection,
    rent_id: int,
    status: str,
) -> None:
    """Обновить статус аренды."""
    await db.execute(
        "UPDATE rents SET status = ? WHERE id = ?",
        (status, rent_id),
    )
    await db.commit()


async def extend_rent(
    db: aiosqlite.Connection,
    rent_id: int,
    additional_hours: int,
) -> Optional[datetime]:
    """Продлить аренду на N часов. Возвращает новую дату истечения."""
    rent = await get_rent_by_id(db, rent_id)
    if rent is None or rent.expires_at is None:
        return None

    new_expires = rent.expires_at + timedelta(hours=additional_hours)
    await db.execute(
        "UPDATE rents SET expires_at = ? WHERE id = ?",
        (new_expires.isoformat(), rent_id),
    )
    await db.commit()
    return new_expires


async def get_expired_rents(db: aiosqlite.Connection) -> Sequence[Rent]:
    """Получить аренды с истёкшим сроком."""
    now = datetime.utcnow().isoformat()
    cursor = await db.execute(
        "SELECT * FROM rents WHERE status IN ('active', 'waiting_sms') AND expires_at IS NOT NULL AND expires_at < ?",
        (now,),
    )
    rows = await cursor.fetchall()
    return [_row_to_rent(r) for r in rows]


# ─── SMS ───────────────────────────────────────────────────────────────


async def save_sms(db: aiosqlite.Connection, sms: SMSMessage) -> SMSMessage:
    """Сохранить полученное SMS."""
    now = datetime.utcnow().isoformat()
    cursor = await db.execute(
        "INSERT INTO sms_messages (rent_id, text, code, received_at) VALUES (?, ?, ?, ?)",
        (sms.rent_id, sms.text, sms.code, now),
    )
    await db.commit()
    sms.id = cursor.lastrowid
    sms.received_at = datetime.fromisoformat(now)
    return sms


async def get_sms_by_rent_id(
    db: aiosqlite.Connection,
    rent_id: int,
) -> Sequence[SMSMessage]:
    """Получить все SMS для аренды."""
    cursor = await db.execute(
        "SELECT * FROM sms_messages WHERE rent_id = ? ORDER BY received_at ASC",
        (rent_id,),
    )
    rows = await cursor.fetchall()
    result = []
    for r in rows:
        result.append(SMSMessage(
            id=r[0], rent_id=r[1], text=r[2], code=r[3],
            received_at=datetime.fromisoformat(r[4]) if r[4] else None,
        ))
    return result


async def get_last_sms_code(
    db: aiosqlite.Connection,
    rent_id: int,
) -> Optional[str]:
    """Получить последний SMS-код для аренды."""
    cursor = await db.execute(
        "SELECT code FROM sms_messages WHERE rent_id = ? AND code IS NOT NULL ORDER BY received_at DESC LIMIT 1",
        (rent_id,),
    )
    row = await cursor.fetchone()
    return row[0] if row else None


# ─── Transactions ──────────────────────────────────────────────────────


async def create_transaction(db: aiosqlite.Connection, tx: Transaction) -> Transaction:
    """Создать транзакцию."""
    now = datetime.utcnow().isoformat()
    cursor = await db.execute(
        "INSERT INTO transactions (user_id, amount, type, description, created_at) VALUES (?, ?, ?, ?, ?)",
        (tx.user_id, tx.amount, tx.type, tx.description, now),
    )
    await db.commit()
    tx.id = cursor.lastrowid
    tx.created_at = datetime.fromisoformat(now)
    return tx


async def get_transactions_by_user_id(
    db: aiosqlite.Connection,
    user_id: int,
    limit: int = 20,
) -> Sequence[Transaction]:
    """Получить последние транзакции пользователя."""
    cursor = await db.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    )
    rows = await cursor.fetchall()
    result = []
    for r in rows:
        result.append(Transaction(
            id=r[0], user_id=r[1], amount=r[2], type=r[3],
            description=r[4], created_at=datetime.fromisoformat(r[5]) if r[5] else None,
        ))
    return result


# ─── Утилиты ────────────────────────────────────────────────────────────


def _row_to_rent(row: sqlite3.Row) -> Rent:
    """Преобразовать строку БД в объект Rent."""
    return Rent(
        id=row[0],
        user_id=row[1],
        phone=row[2],
        service=row[3],
        service_name=row[4],
        country=row[5],
        country_id=row[6],
        rent_type=row[7],
        duration_hours=row[8],
        status=row[9],
        hero_activation_id=row[10],
        hero_rent_id=row[11],
        price=row[12],
        created_at=datetime.fromisoformat(row[13]) if row[13] else None,
        expires_at=datetime.fromisoformat(row[14]) if row[14] else None,
    )
