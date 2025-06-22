from typing import Any, AsyncGenerator, Callable
from pydantic import BaseModel
from hooklet.base import BasePilot
from hooklet.types import HookletMessage
from solvexity.trader.base.config_node import ConfigNode
from solvexity.connector.types import OHLCV, Symbol, Trade
from solvexity.logger import SolvexityLogger
from solvexity.utils import str_to_ms
from redis.asyncio import Redis


class InfluxDBWriter(ConfigNode):
    def __init__(self, 
                 pilot: BasePilot, 
                 source: str,
                 influxdb_url: str,
                 influxdb_token: str,
                 influxdb_org: str,
                 influxdb_bucket: str,
                 measurements: list[str] | None = None,
                 node_id: None|str=None,
                 ):
        super().__init__(pilot, [source], lambda message: None, node_id)
        self.influxdb_url = influxdb_url
        self.influxdb_token = influxdb_token
        self.influxdb_org = influxdb_org
        self.influxdb_bucket = influxdb_bucket
        self.measurements = measurements

        self.logger = SolvexityLogger().get_logger(__name__)

    async def on_start(self) -> None:
        
        
        
    def handler_func(self, message: HookletMessage) -> AsyncGenerator[HookletMessage, None]:
        payload = message.payload
        await self.redis.ts().add

    async def on_finish(self) -> None:
        if self.redis:
            await self.redis.close()
            self.redis = None
            
            