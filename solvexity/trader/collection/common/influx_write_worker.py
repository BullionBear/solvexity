import json
import asyncio
from decimal import Decimal
import time
from hooklet.base.types import Job
from hooklet.node.worker import Worker, PushPull
from influxdb_client_3 import InfluxDBClient3, write_client_options, SYNCHRONOUS
from solvexity.trader.payload import TradePayload

class InfluxWriteWorker(Worker):
    def __init__(self, 
                 node_id: str,
                 influxdb_url: str,
                 influxdb_database: str,
                 influxdb_token: str,
                 max_batch_size: int,
                 flush_interval_ms: int,
                 pushpull: PushPull
                 ):
        super().__init__(node_id, pushpull)
        self.influxdb_url = influxdb_url
        self.influxdb_database = influxdb_database
        self.influxdb_token = influxdb_token
        self.influxdb_client: InfluxDBClient3|None = None
        self.max_batch_size = max_batch_size
        self.flush_interval_ms = flush_interval_ms
        self.points = []
        self.last_flush_ms = time.time() * 1000

    async def on_start(self) -> None:
        await super().on_start()
        wco = write_client_options(write_options=SYNCHRONOUS)
        self.logger.info(f"InfluxDB URL: {self.influxdb_url}")
        self.logger.info(f"InfluxDB Database: {self.influxdb_database}")
        self.logger.info(f"InfluxDB Token is: {self.influxdb_token[:10]}...")

        self.influxdb_client = InfluxDBClient3(
            host=self.influxdb_url,
            token=self.influxdb_token,
            database=self.influxdb_database,
            write_client_options=wco,
        )

    async def on_job(self, job: Job) -> int:
        if job.type == "trade":
            payload = TradePayload(**json.loads(job.data, parse_float=Decimal))
            self.logger.info(f"Received trade: {payload.id}")
            await self.on_trade(payload)
            return 0
        return -1

    async def on_trade(self, payload: TradePayload) -> None:
        point = payload.to_point()
        self.points.append(point)
        self.logger.info(f"Added trade to points: {len(self.points)}")
        self.logger.info(f"Still have {self.max_batch_size - len(self.points)} points to go")
        current_ms = time.time() * 1000
        self.logger.info(f"Still have {self.flush_interval_ms - int(current_ms - self.last_flush_ms)} ms to go")
        if len(self.points) >= self.max_batch_size or current_ms - self.last_flush_ms >= self.flush_interval_ms:
            await self.flush()
            self.last_flush_ms = current_ms

    async def flush(self) -> None:
        self.influxdb_client.write(record=self.points)
        self.logger.info(f"Flushed {len(self.points)} points to InfluxDB")
        self.points = []


    async def on_close(self) -> None:
        await super().on_close()
        if self.points:
            await self.flush()
            self.influxdb_client.close()

    async def on_error(self, error: Exception) -> None:
        self.logger.error(f"Error writing to InfluxDB: {error}")
        raise error