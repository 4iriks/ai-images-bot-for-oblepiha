import logging
from urllib.parse import quote

import aiohttp
from aiohttp import web

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://gen.pollinations.ai/image/{prompt}"


async def health(request: web.Request) -> web.Response:
    return web.Response(text="ok")


async def generate(request: web.Request) -> web.Response:
    data = await request.json()
    prompt = data.get("prompt", "")
    key_index = data.get("key_index", 0)
    pollinations_key = data.get("pollinations_key", "")
    model = data.get("model", "flux")
    width = data.get("width", 1024)
    height = data.get("height", 1024)

    encoded_prompt = quote(prompt, safe="")
    url = BASE_URL.format(prompt=encoded_prompt)
    params = {
        "model": model,
        "width": str(width),
        "height": str(height),
    }
    headers = {
        "Authorization": f"Bearer {pollinations_key}",
    }

    # For now, direct request without SOCKS proxy (XRAY not configured yet)
    # When XRAY is set up, we'll route through SOCKS5 on port 10801 + key_index
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, params=params, headers=headers,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status == 402:
                    return web.Response(status=402, text="Key exhausted")
                if resp.status != 200:
                    text = await resp.text()
                    logger.error("Pollinations returned %d: %s", resp.status, text[:1000])
                    return web.Response(status=resp.status, text="Upstream error")

                content_type = resp.content_type or ""
                if "image" not in content_type:
                    return web.Response(status=502, text=f"Non-image response: {content_type}")

                image_data = await resp.read()
                return web.Response(body=image_data, content_type=content_type)
    except Exception as e:
        logger.error("Error generating image: %s", e)
        return web.Response(status=500, text=str(e))


app = web.Application()
app.router.add_get("/health", health)
app.router.add_post("/generate", generate)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)
