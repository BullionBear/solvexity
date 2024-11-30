import time
from solvexity.trader.core import Feed
from redis import Redis
from threading import Thread, Lock, Event
from sqlalchemy.engine import Engine
from queue import Queue, Empty, Full
import json
from solvexity.trader.data import get_key, get_klines, batch_insert_klines
import solvexity.helper
import solvexity.helper.logging as logging

logger = logging.getLogger("feed")


class HistoricalProvider(Feed):
    BATCH_SZ = 128
    MAX_SZ = 1024

    def __init__(self, redis: Redis, sql_engine: Engine, symbol: str, granular: str, start: int, end: int, limit: int, sleep_time: int):
        """
        Args:
            redis (Redis): Redis client instance.
            sql_engine (Engine): SQL Alchemy engine instance.
            symbol (str): The symbol to get kline data for.
            granular (str): The granularity of the kline data.
            start (int): The start time of the kline data in ms.
            end (int): The end time of the kline data in ms.
            limit (int): The maximum number of kline data to get.
            sleep_time (int): The sleep interval (millisecond) between each batch of kline data.
        """
        super().__init__()
        self.redis = redis
        self.sql_engine = sql_engine
        self.symbol = symbol
        self.granular = granular
        self.start = start
        self.end = end
        self.limit = limit
        self.sleep_time = sleep_time

        self._buffer = Queue(maxsize=1)
        self._stop_event = False
        self._lock = Lock()
        self._index = 0
        self._thread = Thread(target=self._stream_data)
        self._thread.daemon = False  # Allow thread to exit with main program
        

    def send(self):
        """
        Stream klines from the buffer and publish them to Redis.
        """
        self._thread.start()
        while not self._stop_event:
            try:
                key = get_key(self.symbol, self.granular)
                kline = self._buffer.get(block=True, timeout=2)
                if kline is None:
                    logger.warning("No kline data available.")
                    return
                self.redis.zadd(key, {json.dumps(kline.dict()): kline.open_time})
                logger.info(f"Insert kline data: {kline}")
                if self.redis.zcard(key) > self.MAX_SZ:
                    logger.info(f"Removing oldest kline data to keep only {self.MAX_SZ} items")
                    self.redis.zremrangebyrank(key, 0, -self.MAX_SZ - 1)
                event = json.dumps({"x": kline.is_closed, "t": kline.open_time, "E": kline.event_time})
                self.redis.publish(key, event)
                yield kline
            except Empty:
                continue

        logger.info("Historical provider stopped streaming.")

    def receive(self):
        """
        Listen to Redis Pub/Sub messages for the current key and yield them.
        """
        key = get_key(self.symbol, self.granular)
        pubsub = self.redis.pubsub()
        pubsub.subscribe(key)

        logger.info(f"Subscribed to Redis Pub/Sub key: {key}")

        try:
            while not self._stop_event:
                message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    logger.info(f"Received message: {message}")
                    yield message
        finally:
            logger.info(f"Unsubscribing from Redis Pub/Sub key: {key}")
            pubsub.unsubscribe()
            pubsub.close()

    def _fetch_and_store_prestart_data(self, granular_ms: int, key: str):
        """Fetch and store historical data before the start time."""
        prestart_ts = (self.start - granular_ms * self.limit) // granular_ms * granular_ms
        preend_ts = (self.start - granular_ms) // granular_ms * granular_ms - 1

        klines = get_klines(self.sql_engine, self.symbol, self.granular, prestart_ts, preend_ts)
        logger.info(f"Storing pre-start data: from {klines[0].open_time} to {klines[-1].open_time}")
        batch_insert_klines(self.redis, key, klines)

    def _fetch_and_stream_klines(self, granular_ms: int):
        """Fetch and stream klines in batches."""
        current_ts = self.start + granular_ms * self.BATCH_SZ * self._index
        key = get_key(self.symbol, self.granular)

        while current_ts < self.end:
            if self._stop_event:
                logger.info("Receive stop event signal.")
                break

            next_ts = min(current_ts + granular_ms * self.BATCH_SZ - 1, self.end)

            klines = get_klines(self.sql_engine, self.symbol, self.granular, current_ts, next_ts)

            for kline in klines:
                if self._stop_event:
                    return
                self._put_to_buffer(kline)
                if self.sleep_time > 0:
                    time.sleep(self.sleep_time / 1000)

            self._index += 1
            current_ts = next_ts + 1

    def _put_to_buffer(self, kline):
        """Put a kline into the buffer, handling the case where the buffer is full."""
        while not self._stop_event:
            try:
                self._buffer.put(kline, block=True, timeout=2)
                break
            except Full:
                logger.warning("Buffer is full, retrying...")

    def _stream_data(self):
        """Main method to stream data."""
        try:
            granular_ms = helper.to_unixtime_interval(self.granular) * 1000
            key = get_key(self.symbol, self.granular)

            self.start = self.start // granular_ms * granular_ms
            self.end = self.end // granular_ms * granular_ms

            if self._index == 0:
                self._fetch_and_store_prestart_data(granular_ms, key)

            self._fetch_and_stream_klines(granular_ms)

        except Exception as e:
            logger.error(f"Error in _stream_data: {e}", exc_info=True)
        finally:
            self._stop_event = True

    def close(self):
        """Signal the provider to stop streaming data."""
        with self._lock:
            self._stop_event = True
        if self._thread.is_alive():
            self._thread.join()
        try:
            time.sleep(1)
            key = get_key(self.symbol, self.granular)
            logger.info(f"Deleting Redis key: {key}")
            self.redis.delete(key)
        except Exception as e:
            logger.error(f"Error cleaning up Redis key: {e}")
        logger.info("Historical stop() finish.")