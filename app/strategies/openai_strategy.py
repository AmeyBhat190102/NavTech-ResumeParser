import json
from openai import AsyncOpenAI

from app.core.config import settings
from app.models.resume import ParsedResume
from app.strategies.base import BaseExtractionStrategy, SYSTEM_PROMPT, build_user_message


class OpenAIExtractionStrategy(BaseExtractionStrategy):
    """Uses OpenAI chat completion (GPT-4o by default) to extract resume data."""

    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())
        self._model = settings.openai_model

    @property
    def strategy_name(self) -> str:
        return f"openai/{self._model}"

    async def extract(self, resume_text: str) -> ParsedResume:
        response = await self._client.chat.completions.create(
            model=self._model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_message(resume_text)},
            ],
        )

        raw_json = response.choices[0].message.content
        data = json.loads(raw_json)
        parsed = ParsedResume(**data)
        parsed.strategy_used = self.strategy_name
        return parsed
