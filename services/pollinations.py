import asyncio
import logging

import aiohttp

from config import settings
from db.models import get_active_key, increment_key_usage, deactivate_key

logger = logging.getLogger(__name__)


class PollinationsService:
    def __init__(self, session: aiohttp.ClientSession):
        self._session = session

    async def generate_image(
        self, prompt: str, model: str = "flux", width: int = 1024, height: int = 1024,
    ) -> bytes | None:
        for _ in range(10):  # max retries across keys
            key_row = await get_active_key()
            if key_row is None:
                logger.error("No active API keys available")
                return None

            payload = {
                "prompt": prompt,
                "key_index": key_row["key_index"],
                "pollinations_key": key_row["key"],
                "model": model,
                "width": width,
                "height": height,
            }

            try:
                async with self._session.post(
                    f"{settings.proxy_url}/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120),
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
                        logger.error("Proxy returned %d for model %s", resp.status, model)
                        return None
            except asyncio.TimeoutError:
                logger.error("Proxy request timed out")
                return None
            except Exception as e:
                logger.error("Proxy error: %s", e)
                return None

        return None
