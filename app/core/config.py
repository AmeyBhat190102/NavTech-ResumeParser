from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class StrategyType(str, Enum):
    LOCAL = "local"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server auth
    app_api_key: SecretStr

    # Strategy selection
    extraction_strategy: StrategyType = StrategyType.OPENAI

    # OpenAI
    openai_api_key: SecretStr
    openai_model: str = "gpt-4o"

    # Anthropic
    anthropic_api_key: SecretStr
    anthropic_model: str = "claude-sonnet-4-20250514"

    # Local HuggingFace
    local_ner_model: str = "dslim/bert-base-NER"
    local_gen_model: str = "mistralai/Mistral-7B-Instruct-v0.2"
    local_device: str = "cpu"


settings = Settings()
