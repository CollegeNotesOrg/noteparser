"""NoteParser - Academic document parser for Markdown and LaTeX conversion."""

from .core import NoteParser
from .exceptions import ParserError, UnsupportedFormatError

__version__ = "0.1.0"
__all__ = ["NoteParser", "ParserError", "UnsupportedFormatError"]