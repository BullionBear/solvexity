import time
from solvexity.trader.core import Feed
from redis import Redis
from sqlalchemy.engine import Engine
from queue import Queue, Empty, Full
import json
from solvexity.trader.model import KLine
import solvexity.helper as helper
import solvexity.helper.logging as logging
from threading import Thread, Condition
from bisect import bisect_left, bisect_right
import pandas as pd


logger = logging.getLogger("feed")


class OfflineSpotFeed(Feed):
    MAX_SZ = 1024  # Maintain the latest 1024 klines in Redis for each symbol and granularity
    def __init__(self, redis: Redis, sql_engine: Engine, start: int, end: int, sleep_time: int):
        super().__init__()
        self.redis = redis
        self.sql_engine = sql_engine
        self.start = start
        self.end = end
        self.sleep_time = sleep_time
        self._GRANDULARS = {
            interval: helper.to_unixtime_interval(interval) * 1000
            for interval in ("1m", "5m", "15m", "30m", "1h", "4h", "1d")
        }
        self._current_time = start // self._GRANDULARS['1m'] * self._GRANDULARS['1m']
        self._cache_keys = set()
        self._queues = {granular: Queue(maxsize=10) for granular in self._GRANDULARS}  # Separate queues for granulars
        self._stop_event = False
        self._condition = Condition()  # Condition variable for signaling
        self._thread = Thread(target=self._subscribe)
        self._thread.start()

    def _get_key(self, symbol: str, granular: str) -> str:
        return f"spot:{symbol}:{granular}:offline"
    
    def _subscribe(self):
        logger.info("OfflineSpotFeed started _subscribe()")
        pubsub = self.redis.pubsub()
        pubsub.psubscribe(f"spot:*:offline")
        try:
            while not self._stop_event:
                message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message['type'] == 'pmessage':
                    channel = message['channel'].decode('utf-8')
                    granular = channel.split(":")[1]
                    data = json.loads(message['data'].decode('utf-8'))
                    with self._condition:  # Synchronize access to queues
                        if granular in self._queues and not self._queues[granular].full():
                            self._queues[granular].put(data)
                            self._condition.notify_all()  # Notify waiting threads
        finally:
            pubsub.punsubscribe()
            pubsub.close()

    def send(self):
        while self._current_time < self.end:
            if self._stop_event:
                return
            self._current_time += self._GRANDULARS['1m']
            for granular, granular_ms in self._GRANDULARS.items():
                if self._current_time % granular_ms == 0:
                    event = json.dumps({"E": "kline_update", "data": {
                        "granular": granular, "current_time": self._current_time}})
                    self.redis.publish(f"spot:{granular}:offline", event)
                    yield event
            if self.sleep_time > 0:
                time.sleep(self.sleep_time / 1000)
        self._stop_event = True
        logger.info("OfflineSpotFeed stopped send()")

    def latest_n_klines(self, symbol: str, granular: str, limit: int) -> list[KLine]:
        granular_ms = self._GRANDULARS[granular]
        end_time = self._current_time // granular_ms * granular_ms
        start_time = end_time - granular_ms * limit
        return self.get_klines(start_time, end_time - 1, symbol, granular) # -1 is to make sure the kline is closed

    
    def get_klines(self, start_time, end_time, symbol, granular) -> list[KLine]:
        """
        Get kline data from the SQL database.

        Args:
            start_time (int): The start time of the kline data in ms.
            end_time (int): The end time of the kline data in ms.
            symbol (str): The symbol to get kline data for.
            granular (str): The granularity of the kline data.

        Returns:
            list[KLine]: The kline data.
        """
        key = self._get_key(symbol, granular)
        self._cache_keys.add(key)
        granular_ms = self._GRANDULARS[granular]
        byte_klines = self.redis.zrangebyscore(key, start_time, end_time)
        total_klines = [KLine(**json.loads(byte_kline.decode('utf-8'))) for byte_kline in byte_klines]
        kline_dict = {k.open_time: k for k in total_klines}
        open_times = [open_time // granular_ms for open_time in sorted(kline_dict.keys())]
        missing_intervals = self.find_missing_intervals(open_times, start_time // granular_ms, end_time // granular_ms)
        for start, end in missing_intervals:
            klines = self._get_klines(symbol, granular, start * granular_ms, (end + 1) * granular_ms - 1)
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
    
    def receive(self, granular: str, timeout: float = 5.0):
        """
        Wait for and return the next message for the specified granular.
        """
        start_time = time.time()
        with self._condition:  # Wait for a relevant message
            while time.time() - start_time < timeout:
                if not self._queues[granular].empty():
                    yield self._queues[granular].get()
                self._condition.wait(timeout=timeout)  # Wait until notified
        raise TimeoutError(f"No message received for granular {granular} within timeout")


    def close(self):
        """Gracefully stop the Online Feed."""
        logger.info("OfflinepotFeed close() is called")
        self._stop_event = True  # stop all operations
        if self._thread.is_alive():
            self._thread.join()
        # Delete Redis key safely
        try:
            time.sleep(1)
            for cache_key in self._cache_keys:
                self.redis.delete(cache_key)
        except Exception as e:
            logger.error(f"Error cleaning up Redis key: {e}")

        logger.info("OfflineSpotFeed close() finished")

    def _get_klines(self, symbol: str, interval: str, start: int, end: int) -> list[KLine]:
        granular_ms = helper.to_unixtime_interval(interval) * 1000
        query = f"""
        SELECT 
            MAX(CASE WHEN row_num_asc = 1 THEN open_time END) AS open_time,               -- Kline open time
            MAX(CASE WHEN row_num_asc = 1 THEN open_px END) AS open_px,                  -- Open price
            MAX(high_px) AS high_px,                                                    -- High price
            MIN(low_px) AS low_px,                                                      -- Low price
            MAX(CASE WHEN row_num_desc = 1 THEN close_px END) AS close_px,              -- Close price
            SUM(base_asset_volume) AS base_asset_volume,                                -- Volume
            MAX(CASE WHEN row_num_desc = 1 THEN close_time END) AS close_time,          -- Kline close time
            SUM(quote_asset_volume) AS quote_asset_volume,                              -- Quote asset volume
            SUM(number_of_trades) AS number_of_trades,                                  -- Number of trades
            SUM(taker_buy_base_asset_volume) AS taker_buy_base_asset_volume,            -- Taker buy base asset volume
            SUM(taker_buy_quote_asset_volume) AS taker_buy_quote_asset_volume,          -- Taker buy quote asset volume
            '0' AS unused_field                                                         -- Unused field
        FROM (
            SELECT 
                FLOOR(open_time / {granular_ms}) AS grandular,
                open_time,
                close_time,
                open_px,
                high_px,
                low_px,
                close_px,
                number_of_trades,
                base_asset_volume,
                taker_buy_base_asset_volume,
                quote_asset_volume,
                taker_buy_quote_asset_volume,
                ROW_NUMBER() OVER (PARTITION BY FLOOR(open_time / {granular_ms}) ORDER BY open_time ASC) AS row_num_asc,
                ROW_NUMBER() OVER (PARTITION BY FLOOR(open_time / {granular_ms}) ORDER BY open_time DESC) AS row_num_desc
            FROM 
                kline
            WHERE 
                symbol = '{symbol}' 
                AND open_time >= {start} 
                AND open_time < {end}
        ) AS ranked_kline
        GROUP BY 
            grandular
        ORDER BY 
            grandular;
        """
        df = pd.read_sql(query, self.sql_engine)
        res = df.values.tolist()
        return [KLine.from_rest(r, interval) for r in res]
    
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
