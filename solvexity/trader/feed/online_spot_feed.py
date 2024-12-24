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


logger = logging.getLogger()


class OnlineSpotFeed(Feed):
    _GRANULARS = {
        interval: helper.to_unixtime_interval(interval) * 1000
        for interval in ("1m", "5m", "15m", "30m", "1h", "4h", "1d")
    }
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

        self._granular_tc = {
            interval: int(time.time() * 1000) // self._GRANULARS[interval]
            for interval in self._GRANULARS
        }

        self._current_time = int(time.time() * 1000)
        self._cache_keys = set()
        self._buffer: Queue = Queue(maxsize=1)
        self._stop_event = False

    def time(self) -> int:
        return self._current_time

    def send(self):
        """
        Retrieve kline data from the buffer and send it to Redis.
        """
        ws_manager = ThreadedWebsocketManager()
        ws_manager.start()  # Start the WebSocket manager
        ws_manager.start_kline_socket(
            symbol="BTCUSDT",
            interval="1m",
            callback=self._kline_helper
        )
        while not self._stop_event:
            try:
                kline = self._buffer.get(block=True, timeout=2)
                if kline is None:
                    logger.warning("Online feed recv stop signal.")
                    break
                self._current_time = kline.event_time
                event = json.dumps({"E": "kline_update", "data": {
                                "granular": "l1m", "current_time": self._current_time}
                                }) # "l1m" is a special case for "less than 1m" granularity
                self.redis.publish(f"spot:{granular}:online", event)
                for granular in self._GRANULARS:
                    if self._is_ts_closed(granular):
                        event = json.dumps({"E": "kline_update", "data": {
                            "granular": granular, "current_time": self._current_time}
                            })
                        self.redis.publish(f"spot:{granular}:online", event)
                        yield event
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error in OnlineSpotFeed: {e}", exc_info=True)
                continue
        if ws_manager.is_alive():
            ws_manager.stop()  # Stop the WebSocket manager
            ws_manager.join()
        logger.info("OnlineSpotFeed stopped send()")

    def _is_ts_closed(self, granular: str) -> bool:
        granular_ms = self._GRANULARS[granular]
        current_tc = self._current_time // granular_ms
        if current_tc > self._granular_tc[granular]:
            self._granular_tc[granular] = current_tc
            return True
        return False

    def get_klines(self, start_time: int, end_time: int, symbol: str, granular: str) -> list[KLine]:
        logger.info(f"Fetching kline data for {symbol} from {helper.to_isoformat(start_time)} to {helper.to_isoformat(end_time)} with granular {granular}")
        key = f"spot:{symbol}:{granular}:online"
        self._cache_keys.add(key)
        granular_ms = self._GRANULARS[granular]
        byte_klines = self.redis.zrangebyscore(key, start_time, end_time)
        total_klines = [KLine(**json.loads(byte_kline.decode('utf-8'))) for byte_kline in byte_klines]
        kline_dict = {k.open_time: k for k in total_klines}
        open_times = [open_time // granular_ms for open_time in sorted(kline_dict.keys())]
        missing_intervals = self.find_missing_intervals(open_times, start_time // granular_ms, end_time // granular_ms)
        for start, end in missing_intervals:
            logger.info(f"Fetching missing kline data for {symbol} from {start * granular_ms} to {end * granular_ms}")
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
        total_klines.sort(key=lambda x: x.open_time, reverse=False)
        return total_klines
    
    def latest_n_klines(self, symbol: str, granular: str, limit: int) -> list[KLine]:
        granular_ms = self._GRANULARS[granular]
        logger.info(f"Latest {limit} klines , current time: {self._current_time}")
        end_time = self._current_time // granular_ms * granular_ms
        start_time = end_time - granular_ms * limit
        return self.get_klines(start_time, end_time - 1, symbol, granular) # -1 is to make sure the kline is closed

    def receive(self, granular: str|None = None):
        """
        Listen to Redis Pub/Sub messages for the current key and yield them.
        """
        if granular is None:
            granular = "l1m"
        key = f"spot:{granular}:online"
        pubsub = self.redis.pubsub()
        pubsub.subscribe(key)

        logger.info(f"Subscribed to Redis Pub/Sub key: {key}")

        try:
            while not self._stop_event:
                message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message['type'] == 'message':
                    channel = message['channel'].decode('utf-8')
                    granular = channel.split(":")[1]
                    data = json.loads(message['data'].decode('utf-8'))
                    self._current_time = data["data"]['current_time']
                    yield data
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

