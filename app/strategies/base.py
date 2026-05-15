from abc import ABC, abstractmethod

from app.models.resume import ParsedResume


# ── Shared system prompt ───────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert resume parser. Given raw resume text, extract structured information and return ONLY valid JSON — no markdown fences, no commentary.

The JSON must conform exactly to this schema:
{
  "contact": {
    "name": string | null,
    "email": string | null,
    "phone": string | null,
    "location": string | null,
    "linkedin": string | null,
    "github": string | null,
    "website": string | null
  },
  "summary": string | null,
  "education": [
    {
      "institution": string,
      "degree": string | null,
      "field_of_study": string | null,
      "graduation_year": string | null,
      "gpa": string | null
    }
  ],
  "experience": [
    {
      "company": string,
      "position": string | null,
      "location": string | null,
      "start_date": string | null,
      "end_date": string | null,
      "duration": string | null,
      "description": [string]
    }
  ],
  "skills": [string],
  "projects": [
    {
      "name": string,
      "description": string | null,
      "technologies": [string],
      "url": string | null
    }
  ],
  "certifications": [
    {
      "name": string,
      "issuer": string | null,
      "date": string | null,
      "url": string | null
    }
  ],
  "languages": [string]
}

Rules:
- Use null for any field you cannot find.
- dates: use ISO-8601 (YYYY-MM) where possible; otherwise preserve original text.
- duration: derive from start/end dates if not explicit (e.g. "1 year 6 months").
- skills: flat list of individual skill strings, no categories.
- description bullets: each bullet point as a separate string in the list.
- Return ONLY the JSON object. No explanation.
"""


def build_user_message(resume_text: str) -> str:
    return f"Parse the following resume:\n\n{resume_text}"


# ── Base strategy ──────────────────────────────────────────────────────────────

class BaseExtractionStrategy(ABC):
    """
    Strategy interface for resume information extraction.

    Each concrete strategy wraps a different LLM backend while exposing
    the same `extract` method, making them interchangeable at runtime.
    """

    @abstractmethod
    async def extract(self, resume_text: str) -> ParsedResume:
        """
        Parse raw resume text and return a structured ParsedResume.

        Args:
            resume_text: Plain text content extracted from the resume file.

        Returns:
            ParsedResume instance with all available fields populated.
        """
        ...

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Human-readable identifier for this strategy."""
        ...
