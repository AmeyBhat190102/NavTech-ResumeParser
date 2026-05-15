import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings, StrategyType
from app.routes.resume import router as resume_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Warm up the extraction strategy at startup.
    For local models this triggers model download / GPU load early
    rather than on the first request.
    """
    logger.info("Starting Resume Parser API")
    logger.info("Active strategy: %s", settings.extraction_strategy)

    if settings.extraction_strategy == StrategyType.LOCAL:
        # Eagerly load heavy local model pipelines
        from app.strategies.factory import get_extraction_strategy
        strategy = get_extraction_strategy()
        # Access cached_property to trigger load
        _ = strategy._ner_pipeline  # noqa: SLF001
        _ = strategy._gen_pipeline  # noqa: SLF001
        logger.info("Local models loaded successfully")

    yield

    logger.info("Resume Parser API shutting down")


app = FastAPI(
    title="Resume Parser API",
    description=(
        "Parse resumes (PDF / DOCX / DOC) using a pluggable extraction strategy: "
        "OpenAI, Anthropic, or a local HuggingFace model."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume_router)
