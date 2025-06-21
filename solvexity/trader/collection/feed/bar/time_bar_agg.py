from typing import Any, AsyncGenerator, Callable
from pydantic import BaseModel
from hooklet.base import BasePilot
from hooklet.types import HookletMessage
from solvexity.trader.base.config_node import ConfigNode
from solvexity.connector.types import OHLCV, Symbol, Trade
from solvexity.logger import SolvexityLogger
from solvexity.utils import str_to_ms

class TimeBarAggregator(ConfigNode):
    def __init__(self, 
                 pilot: BasePilot, 
                 source: str,
                 router: Callable[[HookletMessage], str | None], 
                 interval_ms: int,
                 node_id: None|str=None,
                 ):
        super().__init__(pilot, [source], router, node_id)
        self.interval_ms = interval_ms
        self._count = 0
        self._running_ohlcv: OHLCV | None = None
        self._symbol: Symbol | None = None
        self.logger = SolvexityLogger().get_logger(__name__)

    @classmethod
    def from_config(cls, pilot: BasePilot, config: dict[str, Any]) -> "TimeBarAggregator":
        return cls(pilot, config["source"], config["router"], config["interval_ms"], config["node_id"])