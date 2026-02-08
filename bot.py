import asyncio
import logging

import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from db.database import init_db, close_db
from db.models import add_api_key
from handlers import start, menu, settings as settings_handler, generation, admin
from middlewares.subscription import SubscriptionMiddleware
from services.gemini import GeminiService
from services.pollinations import PollinationsService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Init DB
    await init_db()

    # Seed API keys from env if DB is empty
    for key in settings.pollinations_api_keys:
        await add_api_key(key)

    # Services
    session = aiohttp.ClientSession()
    gemini_service = GeminiService()
    pollinations_service = PollinationsService(session)

    # Inject services via dp for aiogram 3.x kwargs injection
    dp["gemini_service"] = gemini_service
    dp["pollinations_service"] = pollinations_service

    # Middleware
    dp.message.outer_middleware(SubscriptionMiddleware())
    dp.callback_query.outer_middleware(SubscriptionMiddleware())

    # Routers
    dp.include_routers(
        start.router,
        menu.router,
        settings_handler.router,
        generation.router,
        admin.router,
    )

    logger.info("Bot starting...")
    try:
        await dp.start_polling(bot)
    finally:
        await session.close()
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
