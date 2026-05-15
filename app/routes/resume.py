import pathlib
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.auth import verify_api_key
from app.models.resume import ParsedResume
from app.parsers.factory import get_parser, UnsupportedFileTypeError
from app.strategies.base import BaseExtractionStrategy
from app.strategies.factory import get_extraction_strategy

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["resume"])

_MAX_FILE_SIZE_MB = 10
_MAX_FILE_BYTES = _MAX_FILE_SIZE_MB * 1024 * 1024


# ── Dependency: shared strategy instance per process ─────────────────────────

def _get_strategy() -> BaseExtractionStrategy:
    """FastAPI dependency — returns the singleton strategy."""
    return get_extraction_strategy()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/parse",
    response_model=ParsedResume,
    summary="Parse a resume file",
    description=(
        "Upload a resume in PDF, DOCX, or DOC format. "
        "Returns structured JSON with contact info, education, experience, skills, and more."
    ),
)
async def parse_resume(
    file: UploadFile = File(..., description="Resume file (.pdf / .docx / .doc)"),
    _: str = Depends(verify_api_key),
    strategy: BaseExtractionStrategy = Depends(_get_strategy),
) -> ParsedResume:
    # ── Validate extension ────────────────────────────────────────────────────
    suffix = pathlib.Path(file.filename or "").suffix.lower()
    try:
        parser = get_parser(suffix)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc))

    # ── Read & size-check ─────────────────────────────────────────────────────
    file_bytes = await file.read()
    if len(file_bytes) > _MAX_FILE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {_MAX_FILE_SIZE_MB} MB.",
        )

    # ── Extract raw text ──────────────────────────────────────────────────────
    try:
        raw_text = parser.extract_text(file_bytes)
    except Exception as exc:
        logger.exception("Text extraction failed for file '%s'", file.filename)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not extract text from file: {exc}",
        )

    if not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No readable text found in the uploaded file.",
        )

    # ── Run extraction strategy ───────────────────────────────────────────────
    try:
        result = await strategy.extract(raw_text)
    except Exception as exc:
        logger.exception("Extraction strategy '%s' failed", strategy.strategy_name)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Extraction model error: {exc}",
        )

    result.raw_text_length = len(raw_text)
    return result


@router.get("/health", summary="Health check", include_in_schema=False)
async def health() -> dict:
    return {"status": "ok"}
