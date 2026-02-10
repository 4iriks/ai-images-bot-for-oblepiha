import logging

import aiohttp
from aiogram import Bot
from aiogram.enums import ChatMemberStatus

from config import settings

logger = logging.getLogger(__name__)


async def check_subscription(bot: Bot, user_id: int) -> bool:
    if not settings.required_channel:
        return True
    if user_id == settings.admin_id:
        return True
    try:
        member = await bot.get_chat_member(
            chat_id=settings.required_channel, user_id=user_id
        )
        logger.info("User %d subscription status: %s", user_id, member.status)
        return member.status not in (
            ChatMemberStatus.LEFT,
            ChatMemberStatus.KICKED,
        )
    except Exception as e:
        logger.error("Subscription check failed for user %d: %s", user_id, e)
        return False


async def check_bot_started(user_id: int) -> bool:
    if not settings.bot_check_url or not settings.bot_check_api_key:
        return True
    if user_id == settings.admin_id:
        return True
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{settings.bot_check_url}/check",
                params={"telegram_id": user_id},
                headers={"X-API-Key": settings.bot_check_api_key},
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    activated = data.get("exists", False)
                    logger.info("User %d miniapp check: %s", user_id, activated)
                    return activated
                logger.warning("Miniapp check returned %d for user %d", resp.status, user_id)
                return False
    except Exception as e:
        logger.error("Miniapp check failed for user %d: %s", user_id, e)
        return True
