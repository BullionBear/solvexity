from trader.core import DataProvider
from redis import Redis
from threading import Lock, Event
from binance.client import Client as BinanceClient
from binance import ThreadedWebsocketManager
from queue import Queue, Empty, Full
import json
from trader.data import (
    get_key, query_latest_kline, query_kline, batch_insert_klines,
    KLine
)
import helper
import helper.logging as logging
import time

logger = logging.getLogger("data")


class RealtimeProvider(DataProvider):
    BATCH_SZ = 128
    MAX_SZ = 1024

    def __init__(self, redis: Redis, symbol: str, granular: str, limit: int):
        """
        Args:
            redis (Redis): Redis client instance.
            symbol (str): The symbol to get kline data for.
            granular (str): The granularity of the kline data.
            limit (int): The maximum number of kline data to get.
        """
        super().__init__()
        self.redis = redis
        self.client = BinanceClient()

        self.symbol = symbol
        self.granular = granular
        self.limit = limit

        self._buffer = Queue(maxsize=1)
        self._stop_event = Event()
        self._lock = Lock()
        self._index = 0
        self._thread = ThreadedWebsocketManager()

    def send(self):
        """
        Retrieve kline data from the buffer and send it to Redis.
        """
        self._thread.start()  # Start the WebSocket manager
        self._thread.start_kline_socket(
            symbol=self.symbol,
            interval=self.granular,
            callback=self._kline_helper
        )
        while not self._stop_event.is_set():
            try:
                key = get_key(self.symbol, self.granular)
                kline = self._buffer.get(block=True, timeout=2)
                if kline is None:
                    logger.warning("Unable to retrieve kline data.")
                    return

                event = json.dumps({"x": kline.is_closed, "E": kline.event_time})
                self.redis.publish(key, event)
                yield kline
            except Empty:
                continue

        logger.info("Historical provider stopped.")

    def receive(self):
        """
        Listen to Redis Pub/Sub messages for the current key and yield them.
        """
        key = get_key(self.symbol, self.granular)
        pubsub = self.redis.pubsub()
        pubsub.subscribe(key)

        logger.info(f"Subscribed to Redis Pub/Sub key: {key}")

        try:
            while not self._stop_event.is_set():
                message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    logger.info(f"Received message: {message}")
                    yield message
        finally:
            logger.info(f"Unsubscribing from Redis Pub/Sub key: {key}")
            pubsub.unsubscribe()
            pubsub.close()

    def _kline_helper(self, msg: dict):
        if msg.get('e', '') == 'kline':
            key = get_key(self.symbol, self.granular)
            kline = KLine.from_ws(msg['k'], msg['E'])
            self._buffer.put(kline)
            score = kline.open_time
            latest_kline = query_latest_kline(self.redis, self.symbol, self.granular)
            logger.info(f"Latest kline from cache {key}: {latest_kline}")
            if latest_kline is not None and latest_kline.open_time == score:
                logger.info(f"Received kline is duplicate with latest kline: {kline}")
                with self.redis.pipeline() as pipe:
                    pipe.zrem(key, latest_kline.model_dump_json())
                    pipe.zadd(key, {kline.model_dump_json(): score})
                    pipe.execute()
            else:
                logger.info(f"New kline data received: {kline}")
                self.redis.zadd(key, {kline.model_dump_json(): score})

        if self._index == 0:
            self._index += 1
            klines = query_kline(self.redis, self.symbol, self.granular, 0, int(time.time() * 1000))
            first_kline = klines[0]  # the first kline exists and is the oldest
            ts_granular = helper.to_unixtime_interval(self.granular)
            historical_klines = BinanceClient().get_klines(**{
                "symbol": self.symbol,
                "interval": self.granular,
                "startTime": first_kline.open_time - ts_granular * self.limit * 1000,
                "endTime": first_kline.open_time - 1
            })
            logger.info(f"Fetch {len(historical_klines)} historical klines")
            klines = [KLine.from_rest(kline, self.granular) for kline in historical_klines]
            batch_insert_klines(self.redis, key, klines)

    def stop(self):
        """Gracefully stop the Realtime provider."""
        logger.info("RealtimeProvider stop() is called")
        self._stop_event.set()  # Signal to stop all operations

        try:
            self._buffer.put(None, timeout=1)  # Unblock any waiting threads
        except Full:
            pass

        if self._thread.is_alive():
            self._thread.stop()  # Stop the WebSocket manager

        # Delete Redis key safely
        try:
            key = get_key(self.symbol, self.granular)
            self.redis.delete(key)
        except Exception as e:
            logger.error(f"Error cleaning up Redis key: {e}")

        logger.info("RealtimeProvider stop() finished")
