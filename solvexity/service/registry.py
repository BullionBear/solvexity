"""
Eventrix Registry Module

This module provides a registry for Eventrix types that can be deployed through the API.
It ensures that only pre-approved Eventrix types can be instantiated.
"""

import logging
from typing import Dict, Optional, Type

from hooklet.base import BaseEventrix

logger = logging.getLogger(__name__)


class EventrixRegistry:
    """
    Registry for managing available Eventrix types that can be deployed.
    """

    def __init__(self):
        self._registry: Dict[str, Type[BaseEventrix]] = {}

    def register(self, name: str, eventrix_class: Type[BaseEventrix]) -> None:
        """
        Register an Eventrix class with a name.

        Args:
            name: The name to register the Eventrix class under
            eventrix_class: The Eventrix class to register
        """
        if name in self._registry:
            logger.warning(f"Overwriting existing Eventrix type: {name}")

        self._registry[name] = eventrix_class
        logger.info(f"Registered Eventrix type: {name}")

    def get(self, name: str) -> Optional[Type[BaseEventrix]]:
        """
        Get an Eventrix class by name.

        Args:
            name: The name of the registered Eventrix class

        Returns:
            The Eventrix class if found, None otherwise
        """
        return self._registry.get(name)

    def get_all(self) -> Dict[str, Type[BaseEventrix]]:
        """
        Get all registered Eventrix types.

        Returns:
            A dictionary of registered Eventrix types
        """
        return self._registry.copy()

    def has(self, name: str) -> bool:
        """
        Check if an Eventrix type is registered.

        Args:
            name: The name to check

        Returns:
            True if the Eventrix type is registered, False otherwise
        """
        return name in self._registry


# Create the global registry and register available Eventrix types
eventrix_registry = EventrixRegistry()


# For easy imports
__all__ = ["eventrix_registry"]
