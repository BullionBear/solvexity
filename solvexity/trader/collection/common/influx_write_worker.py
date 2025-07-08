from hooklet.base.types import Job
from hooklet.node.worker import Worker
from influxdb_client_3 import InfluxDBClient3, write_client_options, SYNCHRONOUS
from solvexity.trader.payload import TradePayload

class InfluxWriteWorker(Worker):
    def __init__(self, 
                 node_id: str,
                 influxdb_url: str,
                 influxdb_database: str,
                 influxdb_token: str
                 ):
        super().__init__(node_id)
        self.influxdb_url = influxdb_url
        self.influxdb_database = influxdb_database
        self.influxdb_token = influxdb_token
        self.influxdb_client: InfluxDBClient3|None = None

    async def process(self, job: Job) -> int:
        if job.type == "trade":
            self.logger.info(f"Writing trade {job.data} to InfluxDB")
            payload = TradePayload(**job.data)
            point = payload.to_point()
            self.influxdb_client.write(point)
            return 0
        return -1

    async def start(self) -> None:
        await super().start()
        wco = write_client_options(write_options=SYNCHRONOUS)

        self.influxdb_client = InfluxDBClient3(
            host=self.influxdb_url,
            token=self.influxdb_token,
            database=self.influxdb_database,
            write_client_options=wco,
        )

    async def on_finish(self) -> None:
        await super().on_finish()
        self.influxdb_client.close()