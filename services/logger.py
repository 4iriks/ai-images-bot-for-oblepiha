import logging

from aiogram import Bot
from aiogram.types import BufferedInputFile

from config import settings

log = logging.getLogger(__name__)


async def log_generation(
    bot: Bot,
    user_id: int,
    username: str | None,
    original_prompt: str,
    final_prompt: str | None,
    image_data: bytes,
    model: str = "flux",
):
    if not settings.log_chat_id:
        return

    user_line = f"👤 @{username} (ID: <code>{user_id}</code>)" if username else f"👤 ID: <code>{user_id}</code>"
    caption = (
        f"🎨 Модель: <b>{model}</b>\n"
        f"{user_line}\n"
        f"💬 {original_prompt[:300]}"
    )

    try:
        photo = BufferedInputFile(image_data, filename="generation.png")
        await bot.send_photo(
            chat_id=settings.log_chat_id,
            photo=photo,
            caption=caption[:1024],
        )
    except Exception as e:
        log.error("Failed to log generation: %s", e)
