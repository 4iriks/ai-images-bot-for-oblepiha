from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Message, CallbackQuery

from config import settings
from keyboards.inline import subscription_kb
from utils.subscription import check_subscription


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Ignore messages from log chat — bot only sends there
        chat = None
        if isinstance(event, Message):
            chat = event.chat
        elif isinstance(event, CallbackQuery) and event.message:
            chat = event.message.chat
        if chat and settings.log_chat_id and chat.id == settings.log_chat_id:
            return

        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        # Skip check for /start and /admin
        if isinstance(event, Message) and event.text:
            if event.text.startswith("/start") or event.text.startswith("/admin"):
                return await handler(event, data)

        # Skip check for subscription-check callback
        if isinstance(event, CallbackQuery) and event.data == "check_subscription":
            return await handler(event, data)

        bot: Bot = data["bot"]
        if not await check_subscription(bot, user.id):
            text = "Для использования бота необходимо подписаться на канал:"
            if isinstance(event, Message):
                await event.answer(text, reply_markup=subscription_kb())
            elif isinstance(event, CallbackQuery):
                await event.answer("Подпишитесь на канал!", show_alert=True)
            return

        return await handler(event, data)
