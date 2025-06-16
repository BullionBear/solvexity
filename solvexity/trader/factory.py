"""
Trader Factory Module

This module provides a factory for creating trader instances.
"""


from typing import Any
from hooklet.base import BasePilot
from solvexity.logger import get_logger
from solvexity.trader.feed import TradeFeed, TradeFeedConfig
from solvexity.trader.base import ConfigNode


logger = get_logger(__name__)


class TraderFactory:
    """
    Factory for creating trader instances.
    """

    def __init__(self, pilot: BasePilot):
        self.pilot = pilot

    def create(self, name: str, config: dict[str, Any]) -> ConfigNode:
        """
        Create a trader instance from the registry.
        """
        if name == "TradeFeed":
            config = TradeFeedConfig.from_config(config)
            return TradeFeed.from_config(self.pilot, config)
        raise ValueError(f"Feed type {name} not found in registry")

# For easy imports
__all__ = ["TraderFactory"]
