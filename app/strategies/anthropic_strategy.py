import json
import anthropic as anthropic_sdk

from app.core.config import settings
from app.models.resume import ParsedResume
from app.strategies.base import BaseExtractionStrategy, SYSTEM_PROMPT, build_user_message


class AnthropicExtractionStrategy(BaseExtractionStrategy):
    """Uses Anthropic Claude to extract resume data."""

    def __init__(self) -> None:
        self._client = anthropic_sdk.AsyncAnthropic(api_key=settings.anthropic_api_key.get_secret_value())
        self._model = settings.anthropic_model

    @property
    def strategy_name(self) -> str:
        return f"anthropic/{self._model}"

    async def extract(self, resume_text: str) -> ParsedResume:
        message = await self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            temperature=0,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": build_user_message(resume_text)},
            ],
        )

        raw_text = message.content[0].text

        # Strip any accidental markdown fences Claude might include
        raw_text = raw_text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]

        data = json.loads(raw_text)
        parsed = ParsedResume(**data)
        parsed.strategy_used = self.strategy_name
        return parsed
