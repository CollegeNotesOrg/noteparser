"""NoteParser - AI-powered academic document parser for Markdown and LaTeX conversion."""

from .core import NoteParser
from .exceptions import ParserError, UnsupportedFormatError

__version__ = "2.1.0"
__author__ = "Suryansh Sijwali"
__email__ = "suryanshss1011@gmail.com"
__license__ = "MIT"
__description__ = (
    "AI-powered academic document processing with semantic analysis and knowledge extraction"
)

__all__ = ["NoteParser", "ParserError", "UnsupportedFormatError"]
