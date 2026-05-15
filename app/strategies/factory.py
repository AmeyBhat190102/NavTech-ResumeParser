from app.core.config import settings, StrategyType
from app.strategies.base import BaseExtractionStrategy


def get_extraction_strategy() -> BaseExtractionStrategy:
    """
    Factory that returns the configured extraction strategy.

    Strategy is selected via the EXTRACTION_STRATEGY env var.
    Instantiation is deferred to this function so heavy models
    are not loaded until the first request (or at startup via lifespan).
    """
    match settings.extraction_strategy:
        case StrategyType.OPENAI:
            from app.strategies.openai_strategy import OpenAIExtractionStrategy
            return OpenAIExtractionStrategy()

        case StrategyType.ANTHROPIC:
            from app.strategies.anthropic_strategy import AnthropicExtractionStrategy
            return AnthropicExtractionStrategy()

        case StrategyType.LOCAL:
            from app.strategies.local_strategy import LocalModelStrategy
            return LocalModelStrategy()

        case _:
            raise ValueError(
                f"Unknown EXTRACTION_STRATEGY: '{settings.extraction_strategy}'. "
                "Valid options: local, openai, anthropic"
            )
