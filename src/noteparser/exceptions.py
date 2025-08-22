"""Custom exceptions for NoteParser."""


class ParserError(Exception):
    """Base exception for parser errors."""


class UnsupportedFormatError(ParserError):
    """Raised when attempting to parse an unsupported file format."""


class ConversionError(ParserError):
    """Raised when conversion fails."""
