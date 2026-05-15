from app.parsers.base import BaseParser
from app.parsers.pdf_parser import PDFParser
from app.parsers.docx_parser import DOCXParser


_REGISTRY: dict[str, type[BaseParser]] = {
    ".pdf": PDFParser,
    ".docx": DOCXParser,
    ".doc": DOCXParser,   # python-docx handles basic .doc; complex .doc may need LibreOffice
}


class UnsupportedFileTypeError(ValueError):
    pass


def get_parser(extension: str) -> BaseParser:
    """
    Return the appropriate parser for the given file extension.

    Args:
        extension: Lowercase extension including the dot, e.g. '.pdf'

    Raises:
        UnsupportedFileTypeError: If no parser is registered for the extension.
    """
    ext = extension.lower()
    parser_cls = _REGISTRY.get(ext)

    if parser_cls is None:
        supported = ", ".join(_REGISTRY.keys())
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{ext}'. Supported: {supported}"
        )

    return parser_cls()
