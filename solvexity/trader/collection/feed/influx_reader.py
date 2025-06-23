from typing import Any, AsyncGenerator, Callable
from pydantic import BaseModel
from hooklet.base import BasePilot
from hooklet.types import HookletMessage
from solvexity.trader.base.config_node import ConfigNode
from solvexity.trader.payload import TradePayload, InfluxTradeQuery
from solvexity.logger import SolvexityLogger
from solvexity.utils import str_to_ms
from redis.asyncio import Redis
from influxdb_client import InfluxDBClient, WriteOptions
from influxdb_client.client.write_api import ASYNCHRONOUS, WriteApi
from influxdb_client import Point
from aiocache import Cache


class InfluxTradeReaderConfig(BaseModel):
    source: str
    influxdb_url: str
    influxdb_token: str
    influxdb_org: str
    influxdb_bucket: str
    measurement: str

class InfluxTradeReader(ConfigNode):
    def __init__(self, 
                 pilot: BasePilot, 
                 source: str,
                 influxdb_url: str,
                 influxdb_token: str,
                 influxdb_org: str,
                 influxdb_bucket: str,
                 measurement: str,
                 node_id: None|str=None,
                 ):
        super().__init__(pilot, source, node_id)
        self.influxdb_url = influxdb_url
        self.influxdb_token = influxdb_token
        self.influxdb_org = influxdb_org
        self.influxdb_bucket = influxdb_bucket
        self.measurement = measurement
        self.influxdb_client = InfluxDBClient(url=influxdb_url, token=influxdb_token)

    @classmethod
    def from_config(cls, pilot: BasePilot, config: dict[str, Any]) -> "InfluxTradeReader":
        config_obj = InfluxTradeReaderConfig.model_validate(config)
        return cls(
            pilot=pilot,
            source=config_obj.source,
            influxdb_url=config_obj.influxdb_url,
            influxdb_token=config_obj.influxdb_token,
            influxdb_org=config_obj.influxdb_org,
            influxdb_bucket=config_obj.influxdb_bucket,
            measurement=config_obj.measurement,
        )
    

    async def handler_func(self, message: HookletMessage) -> AsyncGenerator[HookletMessage, None]:
        if message.type != "influx_query":
            yield message
            