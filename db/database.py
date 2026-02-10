import os

import aiosqlite

DB_PATH = os.getenv("DB_PATH", "bot.db")

_connection: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global _connection
    if _connection is None:
        _connection = await aiosqlite.connect(DB_PATH)
        _connection.row_factory = aiosqlite.Row
        await _connection.execute("PRAGMA journal_mode=WAL")
    return _connection


async def init_db():
    db = await get_db()
    await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            clarification_enabled INTEGER DEFAULT 1,
            selected_model TEXT DEFAULT 'imagen-4',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            original_prompt TEXT NOT NULL,
            final_prompt TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS model_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            model TEXT NOT NULL,
            used_date TEXT NOT NULL DEFAULT (date('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    # Миграции для существующих таблиц
    migrations = [
        "ALTER TABLE users ADD COLUMN selected_model TEXT DEFAULT 'imagen-4'",
        "UPDATE users SET selected_model = 'imagen-4' WHERE selected_model = 'flux'",
    ]
    for migration in migrations:
        try:
            await db.execute(migration)
        except Exception:
            pass
    await db.commit()


async def close_db():
    global _connection
    if _connection is not None:
        await _connection.close()
        _connection = None
