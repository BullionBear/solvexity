"""
from typing import Any, AsyncGenerator, Callable
from pydantic import BaseModel
from hooklet.base import BasePilot
from hooklet.types import HookletMessage
from solvexity.trader.base.config_node import ConfigNode
from solvexity.trader.payload import TradePayload, InfluxTradeRequest, InfluxTradeReply
from solvexity.logger import SolvexityLogger
from solvexity.utils import str_to_ms
from redis.asyncio import Redis
from influxdb_client import InfluxDBClient, WriteOptions
from influxdb_client.client.write_api import ASYNCHRONOUS, WriteApi
from influxdb_client import Point
from aiocache import Cache
import time


class InfluxTradeReaderConfig(BaseModel):
    source: str
    influxdb_url: str
    influxdb_token: str
    influxdb_org: str
    influxdb_bucket: str
    measurement: str
    node_id: str

class InfluxTradeReader(ConfigNode):
    def __init__(self, 
                 pilot: BasePilot, 
                 source: str,
                 influxdb_url: str,
                 influxdb_token: str,
                 influxdb_org: str,
                 influxdb_bucket: str,
                 measurement: str,
                 router: Callable[[HookletMessage], str],
                 node_id: None|str=None,
                 ):
        super().__init__(pilot, [source], router, node_id)
        self.influxdb_url = influxdb_url
        self.influxdb_token = influxdb_token
        self.influxdb_org = influxdb_org
        self.influxdb_bucket = influxdb_bucket
        self.measurement = measurement
        self.influxdb_client = InfluxDBClient(url=influxdb_url, token=influxdb_token)

    @classmethod
    def from_config(cls, pilot: BasePilot, config: dict[str, Any]) -> "InfluxTradeReader":
        config_obj = InfluxTradeReaderConfig.model_validate(config)
        router = lambda message: f"{config_obj.node_id}.{message.type}"
        return cls(
            pilot=pilot,
            source=config_obj.source,
            influxdb_url=config_obj.influxdb_url,
            influxdb_token=config_obj.influxdb_token,
            influxdb_org=config_obj.influxdb_org,
            influxdb_bucket=config_obj.influxdb_bucket,
            measurement=config_obj.measurement,
            router=router,
            node_id=config_obj.node_id,
        )
    

    async def handler_func(self, message: HookletMessage) -> AsyncGenerator[HookletMessage, None]:
        if message.type == "trade_request":
            message = HookletMessage(
                node_id=message.node_id,
                type="trade_response",
                payload=None,
                start_at=int(time.time() * 1000),
            )
            request = InfluxTradeRequest.model_validate(message.payload)
            reply = self.on_request(request)
            message.payload = InfluxTradeReply(trades=reply)
            message.finish_at = int(time.time() * 1000)
            yield message
        else:
            self.logger.error(f"Invalid message type: {message.type}")
    
    def on_request(self, request: InfluxTradeRequest) -> list[TradePayload]:
        query_api = self.influxdb_client.query_api()
        query_str = f'''
        from(bucket: "{self.influxdb_bucket}")
        |> range(start: -{request.duration}) 
        |> filter(fn: (r) => r["_measurement"] == "{self.measurement}") 
        |> filter(fn: (r) => r["exchange"] == "{request.exchange}") 
        |> filter(fn: (r) => r["symbol"] == "{request.symbol}")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> sort(columns: ["_time"])
        '''
        result = query_api.query_stream(query_str)
        return [TradePayload.from_record(record) for record in result]
        """