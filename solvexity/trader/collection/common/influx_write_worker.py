import json
import asyncio
from decimal import Decimal
import time
from hooklet.base.types import Job
from hooklet.node.worker import Worker, PushPull
from influxdb_client_3 import InfluxDBClient3, write_client_options, ASYNCHRONOUS
from solvexity.trader.payload import TradePayload

class InfluxWriteWorker(Worker):
    def __init__(self, 
                 node_id: str,
                 influxdb_url: str,
                 influxdb_database: str,
                 influxdb_token: str,
                 batch_size: int,
                 flush_interval_seconds: int,
                 pushpull: PushPull
                 ):
        super().__init__(node_id, pushpull)
        self.influxdb_url = influxdb_url
        self.influxdb_database = influxdb_database
        self.influxdb_token = influxdb_token
        self.influxdb_client: InfluxDBClient3|None = None
        self.batch_size = batch_size
        self.flush_interval_seconds = flush_interval_seconds
        self.lock = asyncio.Lock()
        self.points = []
        self.last_flush_time = time.time()

    async def on_start(self) -> None:
        await super().on_start()
        wco = write_client_options(write_options=ASYNCHRONOUS)
        self.logger.info(f"InfluxDB URL: {self.influxdb_url}")
        self.logger.info(f"InfluxDB Database: {self.influxdb_database}")
        self.logger.info("InfluxDB Token is set.")

        self.influxdb_client = InfluxDBClient3(
            host=self.influxdb_url,
            token=self.influxdb_token,
            database=self.influxdb_database,
            write_client_options=wco,
        )

    async def on_job(self, job: Job) -> int:
        if job.type == "trade":
            payload = TradePayload(**json.loads(job.data, parse_float=Decimal))
            await self.on_trade(payload)
            return 0
        return -1

    async def on_trade(self, payload: TradePayload) -> None:
        point = payload.to_point()
        async with self.lock:
            self.points.append(point)
        if len(self.points) >= self.batch_size or time.time() - self.last_flush_time >= self.flush_interval_seconds:
            self.influxdb_client.write(record=self.points)
            async with self.lock:
                self.points = []
            self.last_flush_time = time.time()

    async def on_close(self) -> None:
        await super().on_close()
        self.influxdb_client.close()

    async def on_error(self, error: Exception) -> None:
        self.logger.error(f"Error writing to InfluxDB: {error}")
        raise error