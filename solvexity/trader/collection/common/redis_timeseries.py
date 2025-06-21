from typing import Any, AsyncGenerator, Callable
from pydantic import BaseModel
from hooklet.base import BasePilot
from hooklet.types import HookletMessage
from solvexity.trader.base.config_node import ConfigNode
from solvexity.connector.types import OHLCV, Symbol, Trade
from solvexity.logger import SolvexityLogger
from solvexity.utils import str_to_ms
from redis.asyncio import Redis


class RedisTimeSeriesCache(ConfigNode):
    def __init__(self, 
                 pilot: BasePilot, 
                 source: str,
                 cache_interval_ms: int,
                 cache_size_bytes: int,
                 node_id: None|str=None,
                 ):
        super().__init__(pilot, [source], lambda message: None, node_id)
        self.cache_interval_ms = cache_interval_ms
        self.cache_size_bytes = cache_size_bytes
        self.logger = SolvexityLogger().get_logger(__name__)
        
    def handler_func(self, message: HookletMessage) -> AsyncGenerator[HookletMessage, None]:
        if message.type == "cache":
            yield message
        else:
            yield message
            