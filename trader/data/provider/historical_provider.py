from trader.core import DataProvider
from redis import Redis
from threading import Thread, Lock, Event
from sqlalchemy.engine import Engine
from queue import Queue, Empty
from trader.data import get_key, get_klines, batch_insert_klines
import helper

class HistoricalProvider(DataProvider):
    BATCH_SZ = 1024
    SLEEP_INTERVAL = 0.1
    def __init__(self, redis: Redis, sql_engine: Engine, symbol: str, granular: str, start: int, end: int, limit: int):
        """
        Args:
            redis (Redis): Redis client instance.
            sql_engine (Engine): SQL Alchemy engine instance.
            symbol (str): The symbol to get kline data for.
            granular (str): The granularity of the kline data.
            start (int): The start time of the kline data in ms.
            end (int): The end time of the kline data in ms.
            limit (int): The maximum number of kline data to get.
        """
        super().__init__()
        self.redis = redis
        self.sql_engine = sql_engine
        self.symbol = symbol
        self.granular = granular
        self.start = start
        self.end = end
        self.limit = limit

        self._buffer = Queue(maxsize=1)
        self._stop_event = Event()
        self._lock = Lock()
        self._index = 0
        self._thread = Thread(target=self._stream_data)
        self._thread.daemon = True  # Allow thread to exit with main program
        self._thread.start()
    
    def __next__(self):
        """Retrieve the next item from the buffer."""
        try:
            data = self.buffer.get(timeout=2 * self.SLEEP_INTERVAL)  # Block if buffer is empty
            return data
        except Empty:
            self._stop_event.set()
            raise StopIteration

    def _stream_data(self):
        grandular_ms = helper.to_unixtime_interval(self.granular) * 1000
        key = get_key(self.symbol, self.granular)
        self.start = self.start // grandular_ms * grandular_ms
        self.end = self.end // grandular_ms * grandular_ms
        if self._index == 0:
            prestart_ts = (self.start - grandular_ms * self.limit) // grandular_ms * grandular_ms
            preend_ts = (self.start - grandular_ms) // grandular_ms * grandular_ms - 1
            klines = get_klines(self.sql_engine, self.symbol, self.granular, prestart_ts, preend_ts)
            batch_insert_klines(self.redis, key, klines)
            current = preend_ts + 1
        while not self._stop_event.is_set():
            current = self.start + self._index * self._grandular_ms
            next_ts = min(current + grandular_ms * self.BATCH_SZ, self.end)
            klines = get_klines(self.sql_engine, self.symbol, self.granular, current, next_ts)
            for kline in klines:
                score = kline.event_time
                self.redis.zadd(key, {kline.model_dump_json(): score})
                self.redis.publish(key, 'update')
                if self.redis.zcard(key) > self.Q_SZ:
                    self.redis.zremrangebyrank(key, 0, -self.Q_SZ - 1)
    