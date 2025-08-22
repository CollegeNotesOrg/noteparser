"""Web dashboard for note browsing and management."""

from .api import api_bp
from .app import create_app

__all__ = ["api_bp", "create_app"]
