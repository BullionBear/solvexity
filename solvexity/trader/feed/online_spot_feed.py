from solvexity.trader.core import Feed
from redis import Redis
from binance.client import Client as BinanceClient
from binance import ThreadedWebsocketManager
from queue import Queue, Empty, Full
import json
from solvexity.trader.model import KLine
import solvexity.helper as helper
import solvexity.helper.logging as logging
import time
from bisect import bisect_left, bisect_right


logger = logging.getLogger("feed")


class OnlineSpotFeed(Feed):
    MAX_SZ = 1024 # Maintain the latest 1024 klines in Redis for each symbol and granularity

    def __init__(self, redis: Redis):
        """
        Args:
            redis (Redis): Redis client instance.
            granulars (tuple[str]): The granularities of the kline data.
        """
        super().__init__()
        self.redis: Redis = redis
        self.client: BinanceClient = BinanceClient()

        self._grandulars = {
            interval: helper.to_unixtime_interval(interval) * 1000
            for interval in ("1m", "5m", "15m", "30m", "1h", "4h", "1d")
        }

        self.current_time = -1
        self._cache_keys = set()
        self._buffer: Queue = Queue(maxsize=1)
        self._stop_event = False
        self._thread = ThreadedWebsocketManager()

    def send(self):
        """
        Retrieve kline data from the buffer and send it to Redis.
        """
        self._thread.start()  # Start the WebSocket manager
        self._thread.start_kline_socket(
            symbol="BTCUSDT",
            interval="1m",
            callback=self._kline_helper
        )
        while not self._stop_event:
            try:
                kline = self._buffer.get(block=True, timeout=2)
                if kline is None:
                    logger.warning("Online feed recv stop signal.")
                    raise StopIteration
                self.current_time = kline.event_time
                for granular, granular_ms in self._granulars.items():
                    if kline.is_close and kline.open_time % granular_ms == 0:
                        event = json.dumps({"E": "kline_update", "granular": granular})
                        self.redis.publish(f"spot.{granular}", event)
                        yield event
            except Empty:
                continue

        logger.info("OnlineSpotFeed stopped send()")

    def get_klines(self, start_time, end_time, symbol, granular) -> list[KLine]:
        key = f"spot.{symbol}.{granular}.online"
        self._cache_keys.add(key)
        granular_ms = self._grandulars[granular]
        byte_klines = self.redis.zrangebyscore(key, start_time, end_time)
        total_klines = [KLine(**json.loads(byte_kline.decode('utf-8'))) for byte_kline in byte_klines]
        kline_dict = {k.open_time: k for k in total_klines}
        open_times = [open_time // granular_ms for open_time in sorted(kline_dict.keys())]
        missing_intervals = self.find_missing_intervals(open_times, start_time // granular_ms, end_time // granular_ms)
        for start, end in missing_intervals:
            klines = self.client.get_klines(symbol=symbol, interval=granular, startTime=start * granular_ms, endTime=end * granular_ms)
            klines = [KLine.from_rest(kline, granular) for kline in klines]
            total_klines.extend(klines)
            with self.redis.pipeline() as pipe:
                for k in klines:
                    score = k.open_time  # Use open_time as the score
                    # Queue the insertion command with JSON serialization
                    pipe.zadd(key, {k.model_dump_json(): score})
                # Execute all commands at once
                pipe.execute()
            if self.redis.zcard(key) > self.MAX_SZ:
                logger.info(f"Removing oldest kline data to keep only {self.MAX_SZ} items")
                self.redis.zremrangebyrank(key, 0, -self.MAX_SZ - 1)
        return total_klines
    
    def latest_n_klines(self, symbol: str, granular: str, limit: int) -> list[KLine]:
        granular_ms = self._grandulars[granular]
        end_time = self.current_time // granular_ms * granular_ms
        start_time = end_time - granular_ms * limit
        return self.get_klines(start_time, end_time - 1, symbol, granular) # -1 is to make sure the kline is closed

    def receive(self, granular: str):
        """
        Listen to Redis Pub/Sub messages for the current key and yield them.
        """
        key = f"spot.{granular}"
        pubsub = self.redis.pubsub()
        pubsub.subscribe(key)

        logger.info(f"Subscribed to Redis Pub/Sub key: {key}")

        try:
            while not self._stop_event:
                message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    yield message
        finally:
            logger.info(f"Unsubscribing from Redis Pub/Sub key: {key}")
            pubsub.unsubscribe()
            pubsub.close()

    def _kline_helper(self, msg: dict):
        if msg.get('e', '') == 'kline':
            kline = KLine.from_ws(msg['k'], msg['E'])
            self._buffer.put(kline)

    def close(self):
        """Gracefully stop the Online Feed."""
        logger.info("OnlineSpotFeed close() is called")
        self._stop_event = True  # stop all operations

        try:
            self._buffer.put(None, timeout=1)  # Unblock any waiting threads
        except Full:
            pass

        if self._thread.is_alive():
            self._thread.stop()  # Stop the WebSocket manager

        # Delete Redis key safely
        try:
            time.sleep(1)
            for cache_key in self._cache_keys:
                self.redis.delete(cache_key)
        except Exception as e:
            logger.error(f"Error cleaning up Redis key: {e}")

        logger.info("OnlineSpotFeed close() finished")

    @staticmethod
    def find_missing_intervals(x, start, end):
        # Initialize the result list
        missing_intervals = []

        # Use binary search to find the starting point within the range
        left = bisect_left(x, start)
        right = bisect_right(x, end)

        # Add the first missing interval if necessary
        if left == 0 or x[left - 1] < start:
            current_start = start
        else:
            current_start = x[left - 1] + 1

        # Traverse only relevant portion of the list
        for i in range(left, right):
            if x[i] > current_start:
                missing_intervals.append([current_start, x[i] - 1])
            current_start = x[i] + 1

        # Add the final missing interval, if necessary
        if current_start <= end:
            missing_intervals.append([current_start, end])

        return missing_intervals

