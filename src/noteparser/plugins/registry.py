"""Plugin registry for managing available plugins."""

from typing import Optional

from .base import BasePlugin


class PluginRegistry:
    """Registry for managing available plugins."""

    def __init__(self):
        self._plugins: dict[str, type[BasePlugin]] = {}
        self._course_plugins: dict[str, list[type[BasePlugin]]] = {}
        self._format_plugins: dict[str, list[type[BasePlugin]]] = {}

    def register(self, plugin_class: type[BasePlugin]):
        """Register a plugin class."""
        self._plugins[plugin_class.name] = plugin_class

        # Register by course types
        for course_type in getattr(plugin_class, "course_types", []):
            if course_type not in self._course_plugins:
                self._course_plugins[course_type] = []
            self._course_plugins[course_type].append(plugin_class)

        # Register by supported formats
        for format_type in getattr(plugin_class, "supported_formats", []):
            if format_type not in self._format_plugins:
                self._format_plugins[format_type] = []
            self._format_plugins[format_type].append(plugin_class)

    def get_plugin(self, name: str) -> Optional[type[BasePlugin]]:
        """Get a plugin by name."""
        return self._plugins.get(name)

    def get_plugins_for_course(self, course_type: str) -> list[type[BasePlugin]]:
        """Get all plugins for a specific course type."""
        return self._course_plugins.get(course_type, [])

    def get_plugins_for_format(self, format_type: str) -> list[type[BasePlugin]]:
        """Get all plugins for a specific format."""
        return self._format_plugins.get(format_type, [])

    def list_plugins(self) -> list[str]:
        """List all registered plugin names."""
        return list(self._plugins.keys())

    def list_course_types(self) -> list[str]:
        """List all supported course types."""
        return list(self._course_plugins.keys())

    def list_formats(self) -> list[str]:
        """List all supported formats."""
        return list(self._format_plugins.keys())
