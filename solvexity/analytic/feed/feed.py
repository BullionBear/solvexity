import redis
import binance
import pandas as pd
import json
import bisect
from sqlalchemy.engine import Engine
from solvexity.helper import MethodTracker, to_ms_interval
from solvexity.analytic.model import KLine
from typing import Optional


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
    def __init__(self, cache: Optional[redis.Redis] = None, enable_tracking: bool = False):
        self.client: binance.Client = binance.Client()
        self.redis: Optional[redis.Redis] = cache
        self.cache_keys: set[str] = set()
        
        # Initialize tracker
        self.tracker = MethodTracker()
        self._tracking_enabled = enable_tracking
        
        # Apply tracking to methods if enabled
        if self._tracking_enabled:
            self._apply_tracking()
    
    def _apply_tracking(self) -> None:
        """Apply tracking to all methods that should be tracked."""
        self._request_binance_klines = self.tracker.track(self._request_binance_klines)
        self._request_cache_klines = self.tracker.track(self._request_cache_klines)
        self._request_local_klines = self.tracker.track(self._request_local_klines)
        self._request_klines = self.tracker.track(self._request_klines)
        self.get_klines = self.tracker.track(self.get_klines)
    
    def enable_tracking(self) -> None:
        """Enable method tracking."""
        if not self._tracking_enabled:
            self._tracking_enabled = True
            self._apply_tracking()
            self.tracker.enable()
    
    def disable_tracking(self) -> None:
        """Disable method tracking."""
        if self._tracking_enabled:
            self._tracking_enabled = False
            self.tracker.disable()
    
    def reset_tracking(self) -> None:
        """Reset tracking data."""
        self.tracker.reset()
    
    def get_tracking_summary(self) -> dict:
        """Get a summary of tracked methods."""
        return self.tracker.get_summary()
    
    def print_tracking_summary(self) -> None:
        """Print a formatted summary of tracked methods."""
        self.tracker.print_summary()

    def _request_binance_klines(self, symbol: str, interval: str, start_time: int, end_time: int) -> list[KLine]:
        res = self.client.get_klines(symbol=symbol, interval=interval, startTime=start_time, endTime=end_time - 1) # Left inclusive, right exclusive
        return [KLine.from_binance(kline, symbol, interval) for kline in res]
    
    def _get_cache_key(self, symbol: str, interval: str):
        key = f"{symbol}-{interval}"
        self.cache_keys.add(key)
        return key

    def _insert_cache(self, symbol: str, interval: str, klines: list[KLine]) -> int:
        if not klines or self.redis is None:
            return 0
        key = self._get_cache_key(symbol, interval)
        res = self.redis.zadd(key, {kline.model_dump_json(): kline.open_time for kline in klines})
        return res
    
    def _request_cache_klines(self, symbol: str, interval: str, start_time: int, end_time: int) -> list[KLine]:
        if self.redis is None:
            return []
            
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
        # If Redis is not available, go directly to Binance
        if self.redis is None:
            return self._request_binance_klines(symbol, interval, start_time, end_time)
            
        klines = self._request_cache_klines(symbol, interval, start_time, end_time)  # Request data from cache
        interval_ms = to_ms_interval(interval)
        # cache[s, e) = empty
        if not klines:
            s = start_time
            e = max(start_time + interval_ms * self.INTERVAL_CACHE_LIMIT[interval], end_time)
            klines = self._request_binance_klines(symbol, interval, s, e)
            self._insert_cache(symbol, interval, klines)
            self._trim_cache(symbol, interval)
            index = bisect.bisect_left([k.open_time for k in klines], end_time)
            return klines[:index]
        # cache[s, e) = kline[i, j)
        # Binance[s, i] + kline[i, j) + Binance[j, e)
        else:
            if start_time < klines[0].open_time:
                s = start_time
                i = klines[0].open_time
                klines = self._request_binance_klines(symbol, interval, s, i) + klines
                self._insert_cache(symbol, interval, klines)
            if end_time > klines[-1].open_time + interval_ms:
                j = klines[-1].open_time
                e = max(end_time, j + interval_ms * self.INTERVAL_CACHE_LIMIT[interval])
                klines += self._request_binance_klines(symbol, interval, j, e)
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
        # Binance[s, i] + kline[i, j) + Binance[j, e)
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
        if self.redis is None:
            return
            
        key = self._get_cache_key(symbol, interval)
        cache_limit = self.INTERVAL_CACHE_LIMIT[interval]
        self.redis.zremrangebyrank(key, 0, -cache_limit - 1)
        return

    def get_klines(self, symbol: str, interval: str, start_time: int, end_time: int) -> pd.DataFrame:
        klines = self._request_klines(symbol, interval, start_time, end_time)
        df = pd.DataFrame([k.model_dump() for k in klines])
        return df
    
    def close(self):
        if self.redis is not None:
            for key in self.cache_keys:
                self.redis.delete(key)
        return
    