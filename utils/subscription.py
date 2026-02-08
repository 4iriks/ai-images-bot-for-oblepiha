import logging

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
    # TODO: Telegram Bot API does not allow checking if a user started another bot.
    # Options: shared DB, API on the VPN bot side, or skip this check.
    return True
