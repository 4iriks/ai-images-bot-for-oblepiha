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
):
    if not settings.log_chat_id:
        return

    caption = (
        f"👤 {username or 'N/A'} (ID: {user_id})\n"
        f"💬 {original_prompt[:200]}\n"
    )
    if final_prompt and final_prompt != original_prompt:
        caption += f"🎯 {final_prompt[:200]}"

    try:
        photo = BufferedInputFile(image_data, filename="generation.png")
        await bot.send_photo(
            chat_id=settings.log_chat_id,
            photo=photo,
            caption=caption[:1024],
        )
    except Exception as e:
        log.error("Failed to log generation: %s", e)
