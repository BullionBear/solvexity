import redis
import binance
import sqlalchemy

from .model import KLine


class Feed:
    def __init__(self, cache: redis.Redis):
        self.client = binance.Client()
        self.redis = cache
        pass

    def _request_binance_klines(self, symbol: str, interval: str, start_time: int, end_time: int) -> list[KLine]:
        self.client.get_klines(symbol=symbol, interval=interval, start_time=start_time, end_time=end_time)
        pass

    def _request_sql_klines(self, symbol: str, interval: str, limit: int):
        pass

    def get_klines(self, symbol: str, interval: str, limit: int):
        pass