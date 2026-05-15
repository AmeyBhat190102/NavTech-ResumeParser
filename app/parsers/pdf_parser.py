import io
import fitz  # PyMuPDF

from app.parsers.base import BaseParser


class PDFParser(BaseParser):
    """Extracts text from PDF files using PyMuPDF."""

    def extract_text(self, file_bytes: bytes) -> str:
        text_parts: list[str] = []

        with fitz.open(stream=io.BytesIO(file_bytes), filetype="pdf") as doc:
            for page in doc:
                text_parts.append(page.get_text("text"))

        return "\n".join(text_parts).strip()
