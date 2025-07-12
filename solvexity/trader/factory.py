"""
Trader Factory Module

This module provides a factory for creating trader instances.
"""


from typing import Any
from hooklet.base import Pilot
from hooklet.base.node import Node
from solvexity.logger import SolvexityLogger
from solvexity.trader.collection.feed import TradeFeed
from solvexity.trader.collection.common import JobDispatcher, InfluxWriteWorker, DebugNode


logger = SolvexityLogger().get_logger(__name__)


class TraderFactory:
    """
    Factory for creating trader instances.
    """

    def __init__(self, pilot: Pilot):
        self.pilot = pilot
        self._registry = {
            # common
            "JobDispatcher": JobDispatcher,
            "InfluxWriteWorker": InfluxWriteWorker,
            "DebugNode": DebugNode,
            # feed
            "TradeFeed": TradeFeed,
        }

    @property
    def available_nodes(self) -> list[str]:
        return list(self._registry.keys())

    def create(self, name: str, config: dict[str, Any]) -> Node:
        """
        Create a trader instance from the registry.
        """
        if name == "JobDispatcher":
            return JobDispatcher(
                config["node_id"], 
                config["subscribes"], 
                self.pilot.pubsub(), 
                self.pilot.pushpull(), 
                config["dispatch_to"])
        elif name == "InfluxWriteWorker":
            return InfluxWriteWorker(
                config["node_id"],
                config["influxdb_url"],
                config["influxdb_database"],
                config["influxdb_token"],
                config["max_batch_size"],
                config["flush_interval_ms"],
                self.pilot.pushpull())
        elif name == "TradeFeed":
            router = lambda msg: f"{config["node_id"]}.{msg.type}"
            return TradeFeed(config["node_id"], 
                             self.pilot.pubsub(), 
                             config["symbol"], 
                             config["exchange"], 
                             router,
                             config["max_batch_size"],
                             config["flush_interval_ms"])
        elif name == "DebugNode":
            return DebugNode(config["node_id"], config["subscribes"], self.pilot.pubsub())
        else:
            raise ValueError(f"Node type {name} not found in registry")

# For easy imports
__all__ = ["TraderFactory"]
