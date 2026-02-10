import asyncio
import logging
from urllib.parse import quote

import aiohttp

from config import settings

logger = logging.getLogger(__name__)


class GenerationError:
    """Результат неудачной генерации с типом ошибки."""
    def __init__(self, error_type: str):
        self.error_type = error_type  # "bad_prompt" | "server_error" | "timeout"


class PollinationsService:
    MAX_RETRIES = 3
    RETRY_DELAY = 3  # секунды

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session

    async def generate_image(
        self, prompt: str, model: str = "flux", width: int = 1024, height: int = 1024,
    ) -> bytes | GenerationError:
        """Отправляет GET-запрос на API для генерации изображения."""
        prompt = prompt.replace("#", "")[:1500]
        encoded_prompt = quote(prompt, safe="")
        url = f"{settings.api_url}/image/{encoded_prompt}?model={model}&width={width}&height={height}"
        headers = {"Authorization": f"Bearer {settings.api_token}"}

        logger.debug("URL запроса: %s", url)
        last_status = None
        for attempt in range(1, self.MAX_RETRIES + 1):
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
                            return GenerationError("server_error")

                    last_status = resp.status

                    body = await resp.text()
                    if resp.status == 400:
                        logger.error("Сервис вернул 400 для модели %s: %s", model, body[:2000])
                        return GenerationError("bad_prompt")

                    logger.warning(
                        "Сервис вернул %d для модели %s (попытка %d/%d): %s",
                        resp.status, model, attempt, self.MAX_RETRIES, body[:500],
                    )
            except asyncio.TimeoutError:
                logger.warning(
                    "Таймаут запроса к сервису (попытка %d/%d)", attempt, self.MAX_RETRIES,
                )
                last_status = "timeout"
            except Exception as e:
                logger.warning(
                    "Ошибка сервиса: %s (попытка %d/%d)", e, attempt, self.MAX_RETRIES,
                )
                last_status = "exception"

            if attempt < self.MAX_RETRIES:
                await asyncio.sleep(self.RETRY_DELAY)

        logger.error("Все %d попыток для модели %s исчерпаны (последний статус: %s)", self.MAX_RETRIES, model, last_status)
        if last_status == "timeout":
            return GenerationError("timeout")
        return GenerationError("server_error")
