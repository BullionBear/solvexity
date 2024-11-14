from trader.core import DataProvider
from redis import Redis
from sqlalchemy.engine import Engine

class HistoricalProvider(DataProvider):
    def __init__(self, redis: Redis, sql_engine: Engine, symbol: str, granular: str, start: int, end: int):
        """
        Args:
            redis (Redis): Redis client instance.
            sql_engine (Engine): SQL Alchemy engine instance.
            symbol (str): The symbol to get kline data for.
            granular (str): The granularity of the kline data.
            start (int): The start time of the kline data in ms.
            end (int): The end time of the kline data in ms.
        """
        super().__init__()
        self.redis = redis
        self.sql_engine = sql_engine
        self.symbol = symbol
        self.granular = granular
        self.start = start
        self.end = end

    