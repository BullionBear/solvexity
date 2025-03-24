import redis
import binance
import pandas as pd
import json
import bisect
from sqlalchemy.engine import Engine

from solvexity.analytic.model import KLine
from solvexity.helper import to_ms_interval

from .query import generate_kline_aggregation_query


class Feed:
    INTERVAL_CACHE_LIMIT = {
        "1m": 60 * 24, # 1 day
        "5m": 12 * 24 * 5, # 5 days
        "15m": 4 * 24 * 15, # 15 days
        "30m": 2 * 24 * 30, # 30 days
        "1h": 24 * 60, # 60 days
        "4h": 6 * 120, # 120 days
        "1d": 365 * 2, # 2 year
    }
    def __init__(self, cache: redis.Redis, sql_engine: Engine):
        self.client: binance.Client = binance.Client()
        self.redis: redis.Redis = cache
        self.sql_engine: Engine = sql_engine
        self.cache_keys: set[str] = set()

    def _request_binance_klines(self, symbol: str, interval: str, start_time: int, end_time: int) -> list[KLine]:
        res = self.client.get_klines(symbol=symbol, interval=interval, startTime=start_time, endTime=end_time - 1) # Left inclusive, right exclusive
        return [KLine.from_binance(kline, symbol, interval) for kline in res]

    def _request_sql_klines(self, symbol: str, interval: str, start_time: int, end_time: int) -> list[KLine]:
        interval_ms = to_ms_interval(interval)
        query = generate_kline_aggregation_query(symbol, interval_ms, start_time, end_time)
        df = pd.read_sql(query, self.sql_engine)
        res = df.values.tolist()
        return [KLine.from_binance(kline, symbol, interval) for kline in res]
    
    def _get_cache_key(self, symbol: str, interval: str):
        key = f"{symbol}-{interval}"
        self.cache_keys.add(key)
        return key

    def _insert_cache(self, symbol: str, interval: str, klines: list[KLine]) -> int:
        key = self._get_cache_key(symbol, interval)
        res = self.redis.zadd(key, {kline.model_dump_json(): kline.open_time for kline in klines})
        return res
    
    def _request_cache_klines(self, symbol: str, interval: str, start_time: int, end_time: int) -> list[KLine]:
        key = self._get_cache_key(symbol, interval)
        res = self.redis.zrangebyscore(key, start_time, f'({end_time}', start=0, num=-1, withscores=False)
        
        # Decode and parse the data into KLine objects
        klines = []
        for kline in res:
            try:
                # Assuming the data is stored as a JSON string
                kline_data = json.loads(kline.decode())
                klines.append(KLine(**kline_data))
            except (json.JSONDecodeError, AttributeError) as e:
                print(f"Error decoding kline data: {e}")
                continue
        return klines
    
    def _request_local_klines(self, symbol: str, interval: str, start_time: int, end_time: int) -> list[KLine]:
        klines = self._request_cache_klines(symbol, interval, start_time, end_time)  # Request data from cache
        interval_ms = to_ms_interval(interval)
        # cache[s, e) = empty
        if not klines:
            s = start_time
            e = max(start_time + interval_ms * self.INTERVAL_CACHE_LIMIT[interval], end_time)
            klines += self._request_sql_klines(symbol, interval, s, e)
            self._insert_cache(symbol, interval, klines)
            self._trim_cache(symbol, interval)
            index = bisect.bisect_left([k.open_time for k in klines], end_time)
            return klines[:index]
        # cache[s, e) = kline[i, j)
        # SQL[s, i] + kline[i, j) + SQL[j, e)
        else:
            if start_time < klines[0].open_time:
                s = start_time
                i = klines[0].open_time
                klines = self._request_sql_klines(symbol, interval, s, i) + klines
                self._insert_cache(symbol, interval, klines)
            if end_time > klines[-1].open_time + interval_ms:
                j = klines[-1].open_time
                e = max(end_time, j + interval_ms * self.INTERVAL_CACHE_LIMIT[interval])
                klines += self._request_sql_klines(symbol, interval, j, e)
                self._insert_cache(symbol, interval, klines)
            self._trim_cache(symbol, interval)
            index = bisect.bisect_left([k.open_time for k in klines], end_time)
            return klines[:index]
    
    def _request_klines(self, symbol: str, interval: str, start_time: int, end_time: int) -> list[KLine]:
        klines = self._request_local_klines(symbol, interval, start_time, end_time)  # Request data from cache
        interval_ms = to_ms_interval(interval)
        # local[s, e) = empty
        if not klines:
            s = start_time
            e = end_time
            klines += self._request_binance_klines(symbol, interval, s, e)
            self._insert_cache(symbol, interval, klines)
            self._trim_cache(symbol, interval)
            index = bisect.bisect_left([k.open_time for k in klines], end_time)
            return klines[:index]
        # cache[s, e) = kline[i, j)
        # SQL[s, i] + kline[i, j) + SQL[j, e)
        else:
            if start_time < klines[0].open_time:
                s = start_time
                i = klines[0].open_time
                klines = self._request_binance_klines(symbol, interval, s, i) + klines
                self._insert_cache(symbol, interval, klines)
            if end_time > klines[-1].open_time + interval_ms:
                j = klines[-1].open_time
                e = end_time
                klines += self._request_binance_klines(symbol, interval, j, e)
                self._insert_cache(symbol, interval, klines)
            self._trim_cache(symbol, interval)
            index = bisect.bisect_left([k.open_time for k in klines], end_time)
            return klines[:index]

    
    def _trim_cache(self, symbol: str, interval: str):
        key = self._get_cache_key(symbol, interval)
        cache_limit = self.INTERVAL_CACHE_LIMIT[interval]
        self.redis.zremrangebyrank(key, 0, -cache_limit - 1)
        return

    def get_klines(self, symbol: str, interval: str, start_time: int, end_time: int) -> list[KLine]:
        return self._request_klines(symbol, interval, start_time, end_time)
    
    def clean_cache(self):
        for key in self.cache_keys:
            self.redis.delete(key)
        return
    