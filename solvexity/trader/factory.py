"""
Trader Factory Module

This module provides a factory for creating trader instances.
"""


from typing import Any
from hooklet.base import Pilot
from hooklet.base.node import Node
from solvexity.logger import SolvexityLogger
from solvexity.trader.collection.feed import TradeFeed


logger = SolvexityLogger().get_logger(__name__)


class TraderFactory:
    """
    Factory for creating trader instances.
    """

    def __init__(self, pilot: Pilot):
        self.pilot = pilot
        self._registry = {
            "TradeFeed": TradeFeed,
        }

    @property
    def available_nodes(self) -> list[str]:
        return list(self._registry.keys())

    def create(self, name: str, config: dict[str, Any]) -> Node:
        """
        Create a trader instance from the registry.
        """
        if name in self._registry:
            node_class = self._registry[name]

            return node_class(config["node_id"], self.pilot.pubsub(), config["symbol"], lambda msg: msg.type)
        raise ValueError(f"Node type {name} not found in registry")

# For easy imports
__all__ = ["TraderFactory"]
