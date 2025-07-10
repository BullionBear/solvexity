import json
import sys
from decimal import Decimal
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
                 pushpull: PushPull
                 ):
        super().__init__(node_id, pushpull)
        self.influxdb_url = influxdb_url
        self.influxdb_database = influxdb_database
        self.influxdb_token = influxdb_token
        self.influxdb_client: InfluxDBClient3|None = None

    async def on_start(self) -> None:
        await super().on_start()
        wco = write_client_options(write_options=ASYNCHRONOUS)
        self.logger.info(f"InfluxDB URL: {self.influxdb_url}")
        self.logger.info(f"InfluxDB Database: {self.influxdb_database}")
        self.logger.info(f"InfluxDB Token: {self.influxdb_token[:10]}...")

        self.influxdb_client = InfluxDBClient3(
            host=self.influxdb_url,
            token=self.influxdb_token,
            database=self.influxdb_database,
            write_client_options=wco,
        )

    async def on_job(self, job: Job) -> int:
        if job.type == "trade":
            self.logger.info(f"Writing trade {job.data} to InfluxDB")
            payload = TradePayload(**json.loads(job.data, parse_float=Decimal))
            point = payload.to_point()
            self.influxdb_client.write(record=point)
            self.logger.info(f"Trade {payload.symbol} {payload.price} written to InfluxDB")
            return 0
        return -1

    

    async def on_close(self) -> None:
        await super().on_close()
        self.influxdb_client.close()

    async def on_error(self, error: Exception) -> None:
        self.logger.error(f"Error writing to InfluxDB: {error}")
        sys.exit(1)