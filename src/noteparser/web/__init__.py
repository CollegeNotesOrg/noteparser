"""Web dashboard for note browsing and management."""

from .app import create_app
from .api import api_bp

__all__ = ['create_app', 'api_bp']