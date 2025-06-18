from typing import Any, AsyncGenerator, Callable
from pydantic import BaseModel
from hooklet.base import BasePilot
from hooklet.types import HookletMessage
from solvexity.trader.base.config_node import ConfigNode
from solvexity.connector.types import OHLCV, Symbol
from solvexity.logger import SolvexityLogger

class OHLCVAggregatorConfig(BaseModel):
    source: str
    interval_ms: int
    node_id: None|str=None


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
                config_obj.exchange.value,
                config_obj.symbol.base_currency,
                config_obj.symbol.quote_currency,
                config_obj.symbol.instrument_type.value
            ]
            return ".".join(components)
        return cls(pilot, config_obj.source, create_router_path, config_obj.interval_ms, config_obj.node_id)

    async def handle_message(self, message: HookletMessage) -> AsyncGenerator[HookletMessage, None]:
        if message.type == "trade":
            self.logger.info(f"Received trade: {message.payload}")
            yield message
        else:
            self.logger.error(f"Received unknown message type: {message.type}")

