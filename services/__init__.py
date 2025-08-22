"""
Microservices module for noteparser integrations.

This module contains the service layer for various AI/ML integrations.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """Registry for managing microservices."""

    def __init__(self):
        self._services: dict[str, Any] = {}
        self._health_checks: dict[str, bool] = {}

    def register(self, name: str, service: Any) -> None:
        """Register a new service."""
        self._services[name] = service
        self._health_checks[name] = False
        logger.info(f"Registered service: {name}")

    def get(self, name: str) -> Any | None:
        """Get a registered service."""
        return self._services.get(name)

    def health_check(self, name: str) -> bool:
        """Check health of a specific service."""
        if name not in self._services:
            return False

        service = self._services[name]
        if hasattr(service, "health_check"):
            self._health_checks[name] = service.health_check()

        return self._health_checks.get(name, False)

    def get_all_health_status(self) -> dict[str, bool]:
        """Get health status of all services."""
        return {name: self.health_check(name) for name in self._services}


# Global service registry
registry = ServiceRegistry()
