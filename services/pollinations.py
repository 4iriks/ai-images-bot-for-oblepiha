import asyncio
import logging
from urllib.parse import quote

import aiohttp

from config import settings

logger = logging.getLogger(__name__)


class PollinationsService:
    def __init__(self, session: aiohttp.ClientSession):
        self._session = session

    async def generate_image(
        self, prompt: str, model: str = "flux", width: int = 1024, height: int = 1024,
    ) -> bytes | None:
        """Отправляет GET-запрос на API для генерации изображения."""
        encoded_prompt = quote(prompt, safe="")
        url = f"{settings.api_url}/image/{encoded_prompt}?model={model}&width={width}&height={height}"
        headers = {"Authorization": f"Bearer {settings.api_token}"}

        try:
            async with self._session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status == 200:
                    content_type = resp.content_type or ""
                    if "image" in content_type:
                        return await resp.read()
                    else:
                        logger.warning("Не изображение от сервиса: %s", content_type)
                        return None
                else:
                    logger.error("Сервис вернул %d для модели %s", resp.status, model)
                    return None
        except asyncio.TimeoutError:
            logger.error("Таймаут запроса к сервису")
            return None
        except Exception as e:
            logger.error("Ошибка сервиса: %s", e)
            return None
