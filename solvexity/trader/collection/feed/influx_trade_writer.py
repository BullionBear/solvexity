"""
from typing import Any, AsyncGenerator, Callable
from pydantic import BaseModel
from hooklet.base import BasePilot
from hooklet.types import HookletMessage
from solvexity.trader.base.config_node import ConfigNode
from solvexity.trader.payload import TradePayload
from solvexity.logger import SolvexityLogger
from solvexity.utils import str_to_ms
from redis.asyncio import Redis
from influxdb_client import InfluxDBClient, WriteOptions
from influxdb_client.client.write_api import ASYNCHRONOUS, WriteApi
from influxdb_client import Point
from aiocache import Cache


class InfluxTradeWriterConfig(BaseModel):
    source: str
    influxdb_url: str
    influxdb_token: str
    influxdb_org: str
    influxdb_bucket: str
    measurement: str
    node_id: str
    tags: dict[str, str] | None = None


class InfluxTradeWriter(ConfigNode):
    def __init__(self, 
                 pilot: BasePilot, 
                 source: str,
                 influxdb_url: str,
                 influxdb_token: str,
                 influxdb_org: str,
                 influxdb_bucket: str,
                 measurement: str,
                 tags: dict[str, str] | None = None,
                 node_id: None|str=None,
                 ):
        super().__init__(pilot, [source], lambda message: None, node_id)
        self.influxdb_url = influxdb_url
        self.influxdb_token = influxdb_token
        self.influxdb_org = influxdb_org
        self.influxdb_bucket = influxdb_bucket
        self.measurement = measurement
        self.tags = tags if tags is not None else {}
        self.influxdb_client: InfluxDBClient | None = None
        self.write_api: WriteApi | None = None
        self.cache = Cache(Cache.MEMORY, ttl=10) # duplicate cache to avoid writing the same trade multiple times
        self.logger = SolvexityLogger().get_logger(__name__)

    @classmethod
    def from_config(cls, pilot: BasePilot, config: dict[str, Any]) -> "InfluxTradeWriter":
        config_obj = InfluxTradeWriterConfig.model_validate(config)
        return cls(
            pilot=pilot,
            source=config_obj.source,
            influxdb_url=config_obj.influxdb_url,
            influxdb_token=config_obj.influxdb_token,
            influxdb_org=config_obj.influxdb_org,
            influxdb_bucket=config_obj.influxdb_bucket,
            measurement=config_obj.measurement,
            tags=config_obj.tags,
            node_id=config_obj.node_id,
        )

    async def on_start(self) -> None:
        await super().on_start()
        self.influxdb_client = InfluxDBClient(
            url=self.influxdb_url,
            token=self.influxdb_token,
            org=self.influxdb_org,
        )
        self.write_api = self.influxdb_client.write_api(write_options=ASYNCHRONOUS)
        
        
    async def handler_func(self, message: HookletMessage) -> AsyncGenerator[HookletMessage, None]:
        if message.type == "trade":
            trade_payload = TradePayload(**message.payload)
            await self.write_trade(trade_payload)
            yield message  # Yield the original message after processing
        else:
            self.logger.error(f"Invalid message type: {message.type}")
            # Don't yield anything for invalid message types

    async def write_trade(self, trade: TradePayload) -> None:
        if await self.cache.get(trade.id) is not None:
            self.logger.info(f"Trade {trade.id} already written to InfluxDB")
            return
        await self.cache.set(trade.id, trade.id)
        self.logger.info(f"Cache set for trade {trade.id}")
        self.logger.info(f"Writing trade {trade.id} to InfluxDB")
        point = trade.to_point()
        for tag, value in self.tags.items():
            point = point.tag(tag, value)
        self.logger.info(f"Writing trade point {point} to InfluxDB")
        self.write_api.write(self.influxdb_bucket, self.influxdb_org, point)

    async def on_finish(self) -> None:
        self.write_api.close()
        self.influxdb_client.close()
        await super().on_finish()
"""