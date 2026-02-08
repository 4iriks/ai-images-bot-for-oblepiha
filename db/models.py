from db.database import get_db

# Model config: display_name, emoji, daily_limit (0 = unlimited)
MODELS = {
    "flux": {"name": "FLUX", "emoji": "⚡", "limit": 0},
    "zimage": {"name": "ZImage", "emoji": "🖼", "limit": 0},
    "flux-2-dev": {"name": "FLUX 2 Dev", "emoji": "🔬", "limit": 10},
    "imagen-4": {"name": "Imagen 4", "emoji": "🌟", "limit": 10},
    "klein": {"name": "Klein", "emoji": "💎", "limit": 7},
    "klein-large": {"name": "Klein Large", "emoji": "👑", "limit": 3},
    "gptimage": {"name": "GPT Image", "emoji": "🤖", "limit": 3},
}


# --- Users ---

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


# --- Model Usage ---

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


# --- Generations ---

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


# --- API Keys ---

async def get_active_key() -> dict | None:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM api_keys WHERE is_active = 1 AND usage_count < usage_limit ORDER BY usage_count ASC LIMIT 1"
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def increment_key_usage(key_id: int):
    db = await get_db()
    await db.execute(
        "UPDATE api_keys SET usage_count = usage_count + 1 WHERE id = ?", (key_id,)
    )
    await db.commit()


async def deactivate_key(key_id: int):
    db = await get_db()
    await db.execute("UPDATE api_keys SET is_active = 0 WHERE id = ?", (key_id,))
    await db.commit()


async def add_api_key(key: str, usage_limit: int = 1000):
    db = await get_db()
    cursor = await db.execute("SELECT COALESCE(MAX(key_index), -1) + 1 FROM api_keys")
    row = await cursor.fetchone()
    next_index = row[0]
    await db.execute(
        "INSERT OR IGNORE INTO api_keys (key, key_index, usage_limit) VALUES (?, ?, ?)",
        (key, next_index, usage_limit),
    )
    await db.commit()


async def get_all_keys() -> list[dict]:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM api_keys ORDER BY id")
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_keys_usage_percent() -> float:
    """Returns average usage percentage across all active keys."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT usage_count, usage_limit FROM api_keys WHERE is_active = 1"
    )
    rows = await cursor.fetchall()
    if not rows:
        return 100.0
    total_pct = sum(r[0] / r[1] * 100 for r in rows if r[1] > 0)
    return total_pct / len(rows)
