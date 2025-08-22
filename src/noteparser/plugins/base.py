"""Base plugin system for extensible parsing capabilities."""

import importlib.util
import inspect
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class BasePlugin(ABC):
    """Base class for all noteparser plugins."""

    name: str = "base_plugin"
    version: str = "1.0.0"
    description: str = "Base plugin class"
    supported_formats: list[str] = []
    course_types: list[str] = []  # e.g., ['math', 'cs', 'chemistry']

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """Initialize the plugin.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)

    @abstractmethod
    def process_content(self, content: str, metadata: dict[str, Any]) -> dict[str, Any]:
        """Process document content with plugin-specific logic.

        Args:
            content: Document content as string
            metadata: Document metadata dictionary

        Returns:
            Dictionary with processed content and any additional metadata
        """

    def can_handle(self, file_path: Path, metadata: dict[str, Any]) -> bool:
        """Check if this plugin can handle the given file.

        Args:
            file_path: Path to the file
            metadata: File metadata

        Returns:
            True if plugin can handle this file
        """
        # Check file extension
        if self.supported_formats:
            if file_path.suffix.lower() not in self.supported_formats:
                return False

        # Check course type
        if self.course_types:
            course = metadata.get("course", "").lower()
            if not any(course_type in course for course_type in self.course_types):
                return False

        return True

    def validate_config(self) -> list[str]:
        """Validate plugin configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Basic validation
        if not self.name:
            errors.append("Plugin name is required")

        if not self.version:
            errors.append("Plugin version is required")

        return errors

    def get_info(self) -> dict[str, Any]:
        """Get plugin information.

        Returns:
            Dictionary with plugin metadata
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "supported_formats": self.supported_formats,
            "course_types": self.course_types,
            "enabled": self.enabled,
            "config": self.config,
        }


class PluginManager:
    """Manages loading and execution of plugins."""

    def __init__(self, plugin_dirs: Optional[list[Path]] = None):
        """Initialize plugin manager.

        Args:
            plugin_dirs: List of directories to search for plugins
        """
        self.plugin_dirs = plugin_dirs or [
            Path(__file__).parent / "builtin",
            Path.cwd() / "plugins",
            Path.home() / ".noteparser" / "plugins",
        ]
        self.plugins: dict[str, BasePlugin] = {}
        self.load_plugins()

    def load_plugins(self):
        """Load all plugins from plugin directories."""
        for plugin_dir in self.plugin_dirs:
            if plugin_dir.exists():
                self._load_plugins_from_dir(plugin_dir)

    def _load_plugins_from_dir(self, plugin_dir: Path):
        """Load plugins from a specific directory.

        Args:
            plugin_dir: Directory to search for plugins
        """
        for plugin_file in plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue  # Skip private files

            try:
                self._load_plugin_file(plugin_file)
            except Exception as e:
                logger.exception(f"Failed to load plugin {plugin_file}: {e}")

    def _load_plugin_file(self, plugin_file: Path):
        """Load a single plugin file.

        Args:
            plugin_file: Path to plugin file
        """
        # Load module
        spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find plugin classes
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BasePlugin) and obj != BasePlugin:
                    # Instantiate plugin
                    plugin_instance = obj()

                    # Validate plugin
                    errors = plugin_instance.validate_config()
                    if errors:
                        logger.error(f"Plugin {plugin_instance.name} validation failed: {errors}")
                        continue

                    # Register plugin
                    self.plugins[plugin_instance.name] = plugin_instance
                    logger.info(f"Loaded plugin: {plugin_instance.name} v{plugin_instance.version}")

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Get a plugin by name.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None if not found
        """
        return self.plugins.get(name)

    def get_plugins_for_file(self, file_path: Path, metadata: dict[str, Any]) -> list[BasePlugin]:
        """Get all plugins that can handle a specific file.

        Args:
            file_path: Path to the file
            metadata: File metadata

        Returns:
            List of plugins that can handle the file
        """
        applicable_plugins = []

        for plugin in self.plugins.values():
            if plugin.enabled and plugin.can_handle(file_path, metadata):
                applicable_plugins.append(plugin)

        # Sort by priority (if implemented) or name
        applicable_plugins.sort(key=lambda p: p.name)
        return applicable_plugins

    def process_with_plugins(
        self,
        file_path: Path,
        content: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Process content with all applicable plugins.

        Args:
            file_path: Path to the file
            content: Document content
            metadata: Document metadata

        Returns:
            Processed content and metadata
        """
        result = {"content": content, "metadata": metadata.copy(), "plugin_results": {}}

        applicable_plugins = self.get_plugins_for_file(file_path, metadata)

        for plugin in applicable_plugins:
            try:
                plugin_result = plugin.process_content(result["content"], result["metadata"])

                # Update content and metadata
                if "content" in plugin_result:
                    result["content"] = plugin_result["content"]

                if "metadata" in plugin_result:
                    result["metadata"].update(plugin_result["metadata"])

                # Store plugin-specific results
                result["plugin_results"][plugin.name] = plugin_result

                logger.debug(f"Applied plugin {plugin.name} to {file_path}")

            except Exception as e:
                logger.exception(f"Plugin {plugin.name} failed on {file_path}: {e}")
                result["plugin_results"][plugin.name] = {"error": str(e)}

        return result

    def list_plugins(self) -> list[dict[str, Any]]:
        """List all loaded plugins.

        Returns:
            List of plugin information dictionaries
        """
        return [plugin.get_info() for plugin in self.plugins.values()]

    def enable_plugin(self, name: str):
        """Enable a plugin.

        Args:
            name: Plugin name
        """
        if name in self.plugins:
            self.plugins[name].enabled = True
            logger.info(f"Enabled plugin: {name}")

    def disable_plugin(self, name: str):
        """Disable a plugin.

        Args:
            name: Plugin name
        """
        if name in self.plugins:
            self.plugins[name].enabled = False
            logger.info(f"Disabled plugin: {name}")

    def reload_plugins(self):
        """Reload all plugins."""
        self.plugins.clear()
        self.load_plugins()
