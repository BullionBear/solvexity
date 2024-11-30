import time
from solvexity.trader.core import Feed
from redis import Redis
from sqlalchemy.engine import Engine
from queue import Queue, Empty, Full
import json
from solvexity.trader.model import KLine
import solvexity.helper as helper
import solvexity.helper.logging as logging
from bisect import bisect_left, bisect_right
import pandas as pd


logger = logging.getLogger("feed")


class OfflineSpotFeed(Feed):
    BATCH_SZ = 128
    MAX_SZ = 1024

    def __init__(self, redis: Redis, sql_engine: Engine, sleep_time: int):
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
        self.redis: Redis = redis
        self.sql_engine: Engine = sql_engine
        self.sleep_time = sleep_time

        self.current_time = -1
        self._buffer = Queue(maxsize=1)
        self._cache_keys = set()
        self._grandulars = {
            interval: helper.to_unixtime_interval(interval) * 1000
            for interval in ("1m", "5m", "15m", "30m", "1h", "4h", "1d")
        }
        self._stop_event = False

    def send(self):
        """
        Stream klines from the buffer and publish them to Redis.
        """
        self._thread.start()
        while not self._stop_event:
            try:
                kline = self._buffer.get(block=True, timeout=2)
                if kline is None:
                    logger.warning("Offline feed recv stop signal.")
                    raise StopIteration
                self.current_time = kline.event_time
                for granular, granular_ms in self._granulars.items():
                    if kline.is_close and kline.open_time % granular_ms == 0:
                        event = json.dumps({"E": "kline_update", "granular": granular})
                        self.redis.publish(f"spot.{granular}.offline", event)
                        yield event
                yield kline
            except Empty:
                continue

        logger.info("OfflineSpotFeed stopped send()")

    def latest_n_klines(self, symbol: str, granular: str, limit: int) -> list[KLine]:
        granular_ms = self._grandulars[granular]
        end_time = self.current_time // granular_ms * granular_ms
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
        key = f"spot.{symbol}.{granular}.offline"
        self._cache_keys.add(key)
        granular_ms = self._grandulars[granular]
        byte_klines = self.redis.zrangebyscore(key, start_time, end_time)
        total_klines = [KLine(**json.loads(byte_kline.decode('utf-8'))) for byte_kline in byte_klines]
        kline_dict = {k.open_time: k for k in total_klines}
        open_times = [open_time // granular_ms for open_time in sorted(kline_dict.keys())]
        missing_intervals = self.find_missing_intervals(open_times, start_time // granular_ms, end_time // granular_ms)
        for start, end in missing_intervals:
            klines = self._get_klines(symbol, granular, start * granular_ms, end * granular_ms)
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

    def receive(self, granular: str):
        """
        Listen to Redis Pub/Sub messages for the current key and yield them.
        """
        key = f"spot.{granular}.offline"
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


    def close(self):
        """Gracefully stop the Online Feed."""
        logger.info("OfflinepotFeed close() is called")
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
        df = pd.read_sql(query, self.engine)
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
