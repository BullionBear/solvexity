from trader.core import DataProvider
from redis import Redis
from threading import Thread, Lock, Event
from sqlalchemy.engine import Engine
from queue import Queue, Empty, Full
import json
import time
from trader.data import get_key, get_klines, batch_insert_klines
import helper
from helper.logging import get_logger

logger = get_logger("data")


class HistoricalProvider(DataProvider):
    BATCH_SZ = 1024
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
        self._thread.daemon = False  # Allow thread to exit with main program
        self._thread.start()
    
    def __next__(self):
        """Retrieve the next item from the buffer."""
        while not self._stop_event.is_set():
            try:
                return self._buffer.get(block=True, timeout=1)
            except Empty:
                continue
        logger.info("Historical provider stopped.")
        raise StopIteration

    def _fetch_and_store_prestart_data(self, granular_ms: int, key: str):
        """Fetch and store historical data before the start time."""
        prestart_ts = (self.start - granular_ms * self.limit) // granular_ms * granular_ms
        preend_ts = (self.start - granular_ms) // granular_ms * granular_ms - 1

        klines = get_klines(self.sql_engine, self.symbol, self.granular, prestart_ts, preend_ts)
        batch_insert_klines(self.redis, key, klines)

    def _fetch_and_stream_klines(self, granular_ms: int):
        """Fetch and stream klines in batches."""
        current_ts = self.start + granular_ms * self.BATCH_SZ * self._index
        while current_ts < self.end:
            if self._stop_event.is_set():
                logger.info("Receive stop event signal.")
                break

            # Calculate batch timestamps
            next_ts = min(current_ts + granular_ms * self.BATCH_SZ, self.end)

            # Fetch klines for the batch
            klines = get_klines(self.sql_engine, self.symbol, self.granular, current_ts, next_ts)

            # Stream klines to the buffer
            for kline in klines:
                if self._stop_event.is_set():
                    return
                self._put_to_buffer(kline)

            self._index += 1
            current_ts = next_ts

    def _put_to_buffer(self, kline):
        """Put a kline into the buffer, handling the case where the buffer is full."""
        while not self._stop_event.is_set():
            try:
                self._buffer.put(kline, block=True, timeout=1)
                break
            except Full:
                logger.warning("Buffer is full, retrying...")

    def _stream_data(self):
        """Main method to stream data."""
        try:
            granular_ms = helper.to_unixtime_interval(self.granular) * 1000
            key = get_key(self.symbol, self.granular)

            # Align start and end timestamps to the granularity
            self.start = self.start // granular_ms * granular_ms
            self.end = self.end // granular_ms * granular_ms

            # Fetch and store prestart data
            if self._index == 0:
                self._fetch_and_store_prestart_data(granular_ms, key)

            # Fetch and stream data in batches
            self._fetch_and_stream_klines(granular_ms)

        except Exception as e:
            logger.error(f"Error in _stream_data: {e}", exc_info=True)
        finally:
            self._stop_event.set()

    def stop(self):
        """Signal the provider to stop streaming data."""
        with self._lock:
            self._stop_event.set()
        self._thread.join()