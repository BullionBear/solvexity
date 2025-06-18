from abc import ABC, abstractmethod
from typing import Any, Callable

from hooklet.base import BasePilot
from hooklet.types import HookletMessage
from hooklet.eventrix.v2 import Node


class ConfigNode(Node, ABC):
    """
    A node that can be configured from a configuration dictionary.
    """

    def __init__(self, pilot: BasePilot, sources: list[str], router: Callable[[HookletMessage], str], node_id: str):
        super().__init__(pilot, sources, router, node_id)

    @classmethod
    @abstractmethod
    def from_config(cls, pilot: BasePilot, config: dict[str, Any]) -> "ConfigNode":
        pass