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
        self._current_timeslot = -1
        self.logger = SolvexityLogger().get_logger(__name__)

    @classmethod
    def from_config(cls, pilot: BasePilot, config: dict[str, Any]) -> "TimeBarAggregator":
        return cls(pilot, config["source"], config["router"], config["interval_ms"], config["node_id"])
    
    async def handler_func(self, message: HookletMessage) -> AsyncGenerator[HookletMessage, None]:
        if message.type == "trade":
            trade = Trade.model_validate(message.payload)
            async for message in self.on_trade(trade):
                yield message
        else:
            self.logger.error(f"TimeBarAggregator: Invalid message type: {message.type}")

    async def on_trade(self, trade: Trade) -> AsyncGenerator[HookletMessage, None]:
        if self._current_timeslot == -1:
            self._current_timeslot = trade.timestamp
        else:
            if trade.timestamp - self._current_timeslot > self.interval_ms:
                self._current_timeslot = trade.timestamp
                yield HookletMessage(type="bar", payload=self._current_timeslot)
            else:
                yield HookletMessage(type="trade", payload=trade)
            