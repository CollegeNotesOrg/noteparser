"""Plugin system for course-specific parsers and extensions."""

from .base import BasePlugin, PluginManager
from .registry import PluginRegistry

__all__ = ["BasePlugin", "PluginManager", "PluginRegistry"]
