from abc import ABC, abstractmethod


class BaseParser(ABC):
    """Extracts raw text from a resume file."""

    @abstractmethod
    def extract_text(self, file_bytes: bytes) -> str:
        """Return plain-text content from the file bytes."""
        ...
