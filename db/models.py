from db.database import get_db

# Конфиг моделей: display_name, emoji, daily_limit (0 = безлимитно)
MODELS = {
    "flux": {"name": "FLUX", "emoji": "⚡", "limit": 0},
    "zimage": {"name": "ZImage", "emoji": "🖼", "limit": 0},
    "flux-2-dev": {"name": "FLUX 2 Dev", "emoji": "🔬", "limit": 10},
    "imagen-4": {"name": "Imagen 4", "emoji": "🌟", "limit": 10},
    "klein": {"name": "Klein", "emoji": "💎", "limit": 7},
    "klein-large": {"name": "Klein Large", "emoji": "👑", "limit": 3},
    "gptimage": {"name": "GPT Image", "emoji": "🤖", "limit": 3},
}


# --- Пользователи ---

async def ensure_user(user_id: int, username: str | None, full_name: str):
    db = await get_db()
    await db.execute(
        """INSERT INTO users (user_id, username, full_name)
           VALUES (?, ?, ?)
           ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, full_name=excluded.full_name""",
        (user_id, username, full_name),
    )
    await db.commit()


async def get_user(user_id: int) -> dict | None:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def set_clarification(user_id: int, enabled: bool):
    db = await get_db()
    await db.execute(
        "UPDATE users SET clarification_enabled = ? WHERE user_id = ?",
        (int(enabled), user_id),
    )
    await db.commit()


async def set_user_model(user_id: int, model: str):
    db = await get_db()
    await db.execute(
        "UPDATE users SET selected_model = ? WHERE user_id = ?",
        (model, user_id),
    )
    await db.commit()


async def get_user_model(user_id: int) -> str:
    user = await get_user(user_id)
    if user and user.get("selected_model"):
        return user["selected_model"]
    return "flux"


async def get_total_users() -> int:
    db = await get_db()
    cursor = await db.execute("SELECT COUNT(*) FROM users")
    row = await cursor.fetchone()
    return row[0]


# --- Использование моделей ---

async def get_model_usage_today(user_id: int, model: str) -> int:
    db = await get_db()
    cursor = await db.execute(
        "SELECT COUNT(*) FROM model_usage WHERE user_id = ? AND model = ? AND used_date = date('now')",
        (user_id, model),
    )
    row = await cursor.fetchone()
    return row[0]


async def add_model_usage(user_id: int, model: str):
    db = await get_db()
    await db.execute(
        "INSERT INTO model_usage (user_id, model) VALUES (?, ?)",
        (user_id, model),
    )
    await db.commit()


# --- Генерации ---

async def add_generation(user_id: int, original_prompt: str, final_prompt: str | None):
    db = await get_db()
    await db.execute(
        "INSERT INTO generations (user_id, original_prompt, final_prompt) VALUES (?, ?, ?)",
        (user_id, original_prompt, final_prompt),
    )
    await db.commit()


async def get_total_generations() -> int:
    db = await get_db()
    cursor = await db.execute("SELECT COUNT(*) FROM generations")
    row = await cursor.fetchone()
    return row[0]


async def get_today_generations() -> int:
    db = await get_db()
    cursor = await db.execute(
        "SELECT COUNT(*) FROM generations WHERE date(created_at) = date('now')"
    )
    row = await cursor.fetchone()
    return row[0]


async def get_top_prompters(limit: int = 10) -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        """SELECT u.user_id, u.username, u.full_name, COUNT(g.id) as gen_count
           FROM users u
           LEFT JOIN generations g ON u.user_id = g.user_id
           GROUP BY u.user_id
           ORDER BY gen_count DESC
           LIMIT ?""",
        (limit,),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]
