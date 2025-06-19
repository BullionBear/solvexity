from typing import Any, AsyncGenerator, Callable
from pydantic import BaseModel
from hooklet.base import BasePilot
from hooklet.types import HookletMessage
from solvexity.trader.base.config_node import ConfigNode
from solvexity.connector.types import OHLCV, Symbol
from solvexity.logger import SolvexityLogger
from solvexity.utils import str_to_ms

class OHLCVAggregatorConfig(BaseModel):
    source: str
    interval: str
    node_id: str

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "OHLCVAggregatorConfig":
        config_obj = OHLCVAggregatorConfig(**config)
        return config_obj

class OHLCVAggregator(ConfigNode):
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
    def from_config(cls, pilot: BasePilot, config: dict[str, Any]) -> "OHLCVAggregator":
        config_obj = OHLCVAggregatorConfig(**config)
        def create_router_path(e):
            components = [
                e.node_id,
                e.type,
                config_obj.interval
            ]
            return ".".join(components)
        interval_ms = str_to_ms(config_obj.interval)
        return cls(pilot, config_obj.source, create_router_path, interval_ms, config_obj.node_id)

    async def handler_func(self, message: HookletMessage) -> AsyncGenerator[HookletMessage, None]:
        if message.type == "trade":
            self.logger.info(f"Received trade: {message.payload}")
            yield message
        else:
            self.logger.error(f"Received unknown message type: {message.type}")

