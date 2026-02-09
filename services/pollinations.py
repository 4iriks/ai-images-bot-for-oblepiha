import asyncio
import logging

import aiohttp

from config import settings

logger = logging.getLogger(__name__)


class PollinationsService:
    def __init__(self, session: aiohttp.ClientSession):
        self._session = session

    async def generate_image(
        self, prompt: str, model: str = "flux", width: int = 1024, height: int = 1024,
    ) -> bytes | None:
        """Отправляет запрос на генерацию в service-bot (key swap сервис)."""
        payload = {
            "prompt": prompt,
            "model": model,
            "width": width,
            "height": height,
        }

        try:
            async with self._session.post(
                f"{settings.service_url}/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status == 200:
                    content_type = resp.content_type or ""
                    if "image" in content_type:
                        return await resp.read()
                    else:
                        logger.warning("Не изображение от сервиса: %s", content_type)
                        return None
                elif resp.status == 403:
                    logger.error("Сервис не авторизован (ожидает одобрения)")
                    return None
                elif resp.status == 503:
                    logger.error("Нет активных ключей на сервисе")
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
