"""Custom exceptions for NoteParser."""


class ParserError(Exception):
    """Base exception for parser errors."""
    pass


class UnsupportedFormatError(ParserError):
    """Raised when attempting to parse an unsupported file format."""
    pass


class ConversionError(ParserError):
    """Raised when conversion fails."""
    pass