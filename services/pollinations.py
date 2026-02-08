import asyncio
import logging
from urllib.parse import quote

import aiohttp

from db.models import get_active_key, increment_key_usage, deactivate_key

logger = logging.getLogger(__name__)

BASE_URL = "https://image.pollinations.ai/prompt/{prompt}"


class PollinationsService:
    def __init__(self, session: aiohttp.ClientSession):
        self._session = session

    async def generate_image(self, prompt: str) -> bytes | None:
        encoded_prompt = quote(prompt, safe="")

        for _ in range(10):  # max retries across keys
            key_row = await get_active_key()
            if key_row is None:
                logger.error("No active API keys available")
                return None

            url = BASE_URL.format(prompt=encoded_prompt)
            params = {
                "model": "flux",
                "width": 1024,
                "height": 1024,
                "nologo": "true",
                "token": key_row["key"],
            }

            try:
                async with self._session.get(
                    url, params=params, timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    if resp.status == 200:
                        content_type = resp.content_type or ""
                        if "image" in content_type:
                            await increment_key_usage(key_row["id"])
                            return await resp.read()
                        else:
                            logger.warning("Non-image response: %s", content_type)
                            return None
                    elif resp.status == 402:
                        logger.warning("Key %d got 402, deactivating", key_row["id"])
                        await deactivate_key(key_row["id"])
                        continue
                    else:
                        logger.error("Pollinations returned %d", resp.status)
                        return None
            except asyncio.TimeoutError:
                logger.error("Pollinations request timed out")
                return None
            except Exception as e:
                logger.error("Pollinations error: %s", e)
                return None

        return None
