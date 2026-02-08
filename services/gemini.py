import asyncio

from google import genai

from config import settings


class GeminiService:
    def __init__(self):
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = "gemini-2.5-flash-lite-preview-06-17"

    async def generate_clarifying_questions(self, prompt: str) -> str:
        system = (
            "You are an assistant helping a user create a detailed image generation prompt. "
            "The user gave you their idea. Ask 3-5 short clarifying questions to better understand "
            "what they want. Write the questions in the SAME language as the user's prompt. "
            "Number the questions. Do not add any other text."
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

    async def _generate(self, system: str, user_text: str) -> str:
        def _sync():
            response = self._client.models.generate_content(
                model=self._model,
                contents=user_text,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=0.7,
                ),
            )
            return response.text

        return await asyncio.to_thread(_sync)
