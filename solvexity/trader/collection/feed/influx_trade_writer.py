from typing import Any, AsyncGenerator, Callable
from pydantic import BaseModel
from solvexity.trader.payload import TradePayload
from solvexity.logger import SolvexityLogger
from hooklet.node.worker import JobDispatcher
from influxdb_client import InfluxDBClient, WriteOptions
from influxdb_client.client.write_api import ASYNCHRONOUS, WriteApi
from influxdb_client import Point
from aiocache import Cache
from hooklet.types import Msg
from hooklet.node.sinker import Sinker

class InfluxTradeDispatcher(Sinker):
    def __init__(self, 
                 node_id: str,
                 subscribes: list[str],
                 influxdb_url: str,
                 influxdb_token: str,
                 influxdb_org: str,
                 influxdb_bucket: str,
                 measurement: str,
                 ):
        super().__init__(node_id, subscribes)
        self.dispatcher = JobDispatcher(self.pubsub)
        self.influxdb_url = influxdb_url
        self.influxdb_token = influxdb_token
        self.influxdb_org = influxdb_org
        self.influxdb_bucket = influxdb_bucket
        self.influxdb_client = InfluxDBClient(
            url=self.influxdb_url,
            token=self.influxdb_token,
            org=self.influxdb_org,
        )
        self.write_api = self.influxdb_client.write_api(write_options=ASYNCHRONOUS)
        self.measurement = measurement
        self.cache = Cache(Cache.MEMORY, ttl=10) # duplicate cache to avoid writing the same trade multiple times
        self.logger = SolvexityLogger().get_logger(__name__)


    async def on_start(self) -> None:
        await super().on_start()
        
        
    async def sink(self, msg: Msg) -> None:
        if msg.type == "trade":
            trade_payload = TradePayload(**msg.data)
            await self.write_trade(trade_payload)
        else:
            self.logger.error(f"Invalid message type: {msg.type}")

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
