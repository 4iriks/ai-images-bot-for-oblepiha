import base64
import logging

import aiohttp

from config import settings

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self, session: aiohttp.ClientSession):
        self._session = session
        self._model = "gemini-2.5-flash-lite"

    async def generate_clarifying_questions(self, prompt: str) -> str:
        system = (
            "You are an assistant helping a user create a detailed image generation prompt. "
            "The user gave you their idea. Ask 3-5 short clarifying questions to better understand "
            "what they want. Write the questions in the SAME language as the user's prompt. "
            "Number the questions. Do not add any other text."
        )
        return await self._generate(system, prompt)

    async def enhance_prompt_with_image(self, image_data: bytes, prompt: str = "") -> str:
        system = (
            "You are an assistant that creates detailed image generation prompts. "
            "The user sent you a reference image and optionally a text description. "
            "Analyze the image and the text (if provided) and create a single detailed prompt "
            "in ENGLISH for an image generation model. "
            "The prompt should be vivid, specific, and describe the scene, style, lighting, "
            "colors, and composition. Output ONLY the prompt text, nothing else."
        )
        b64 = base64.b64encode(image_data).decode()
        user_content = [
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
            },
        ]
        if prompt:
            user_content.insert(0, {"type": "text", "text": prompt})
        return await self._generate_multimodal(system, user_content)

    async def enhance_prompt(self, prompt: str) -> str:
        system = (
            "You are an assistant that creates detailed image generation prompts. "
            "The user gave you their idea. "
            "Create a single detailed prompt in ENGLISH for an image generation model. "
            "The prompt should be vivid, specific, and describe the scene, style, lighting, "
            "colors, and composition. Output ONLY the prompt text, nothing else."
        )
        return await self._generate(system, prompt)

    async def refine_prompt(self, original_prompt: str, answers: str) -> str:
        system = (
            "You are an assistant that creates detailed image generation prompts. "
            "The user gave you their original idea and answers to clarifying questions. "
            "Create a single detailed prompt in ENGLISH for an image generation model. "
            "The prompt should be vivid, specific, and describe the scene, style, lighting, "
            "colors, and composition. Output ONLY the prompt text, nothing else."
        )
        user_text = f"Original idea: {original_prompt}\n\nAnswers to questions:\n{answers}"
        return await self._generate(system, user_text)

    async def _generate_multimodal(self, system: str, user_content: list) -> str:
        url = f"{settings.api_url}/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.api_token}",
        }
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.7,
        }

        async with self._session.post(
            url,
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                logger.error("Text API error %d: %s", resp.status, text)
                raise RuntimeError(f"Text API returned {resp.status}")
            data = await resp.json()
            return data["choices"][0]["message"]["content"]

    async def _generate(self, system: str, user_text: str) -> str:
        url = f"{settings.api_url}/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.api_token}",
        }
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_text},
            ],
            "temperature": 0.7,
        }

        async with self._session.post(
            url,
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                logger.error("Text API error %d: %s", resp.status, text)
                raise RuntimeError(f"Text API returned {resp.status}")
            data = await resp.json()
            return data["choices"][0]["message"]["content"]
