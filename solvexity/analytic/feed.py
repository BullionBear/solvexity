import redis
import binance
import pandas as pd
import json
from sqlalchemy.engine import Engine

from .model import KLine
from solvexity.helper import to_ms_interval


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

    def _request_binance_klines(self, symbol: str, interval: str, start_time: int, end_time: int) -> list[KLine]:
        res = self.client.get_klines(symbol=symbol, interval=interval, startTime=start_time, endTime=end_time - 1) # Left inclusive, right exclusive
        return [KLine.from_binance(kline, symbol, interval) for kline in res]

    def _request_sql_klines(self, symbol: str, interval: str, start_time: int, end_time: int) -> list[KLine]:
        interval_ms = to_ms_interval(interval)
        query = f"""
        SELECT 
            MAX(CASE WHEN row_num_asc = 1 THEN open_time END) AS open_time,             -- Kline open time
            MAX(CASE WHEN row_num_asc = 1 THEN open_px END) AS open_px,                 -- Open price
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
                FLOOR(open_time / {interval_ms}) AS grandular,
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
                ROW_NUMBER() OVER (PARTITION BY FLOOR(open_time / {interval_ms}) ORDER BY open_time ASC) AS row_num_asc,
                ROW_NUMBER() OVER (PARTITION BY FLOOR(open_time / {interval_ms}) ORDER BY open_time DESC) AS row_num_desc
            FROM 
                kline
            WHERE 
                symbol = '{symbol}' 
                AND open_time >= {start_time} 
                AND open_time < {end_time}
        ) AS ranked_kline
        GROUP BY 
            grandular
        ORDER BY 
            grandular;
        """
        df = pd.read_sql(query, self.sql_engine)
        res = df.values.tolist()
        return [KLine.from_binance(kline, symbol, interval) for kline in res]
    
    def _get_cache_key(self, symbol: str, interval: str):
        return f"{symbol}-{interval}"

    def _insert_cache(self, symbol: str, interval: str, klines: list[KLine]) -> int:
        key = f"{symbol}-{interval}"
        res = self.redis.zadd(key, {kline.model_dump_json(): kline.open_time for kline in klines})
        return res
    
    def _request_cache_klines(self, symbol: str, interval: str, start_time: int, end_time: int) -> list[KLine]:
        key = f"{symbol}-{interval}"
        res = self.redis.zrangebyscore(key, start_time, end_time, start=0, num=-1, withscores=False)
        
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
    
    def trim_cache(self, symbol: str, interval: str):
        key = self._get_cache_key(symbol, interval)
        cache_limit = self.INTERVAL_CACHE_LIMIT[interval]
        self.redis.zremrangebyrank(key, 0, -cache_limit - 1)
        return

    def get_klines(self, symbol: str, interval: str, start_time: int, end_time: int) -> list[KLine]:
        # 0. Reformat timestamps
        interval_ms = to_ms_interval(interval)
        start_time = start_time // interval_ms * interval_ms
        end_time = end_time // interval_ms * interval_ms
        # 1. Request data from cache
        klines = self._request_cache_klines(symbol, interval, start_time, end_time)
        # 2.1. If cache is empty, kline[s, e) = SQL[s, k) + Binance[k, e)
        if not klines:
            # SQL[s, k)
            s = start_time
            k = s + interval_ms * self.INTERVAL_CACHE_LIMIT[interval]
            sql_klines = self._request_sql_klines(symbol, interval, s, k)
            self._insert_cache(symbol, interval, sql_klines)
            # if k > e, return SQL[s, e)
            if sql_klines and sql_klines[-1].open_time >= end_time:
                self._trim_cache(symbol, interval)
                return [kline for kline in sql_klines if kline.open_time < end_time]
            else:
                # Binance[k, e)
                klines += sql_klines
                k = (klines[-1].open_time // interval_ms + 1) * interval_ms
                e = end_time
                binance_klines = self._request_binance_klines(symbol, interval, k, e)
                self._insert_cache(symbol, interval, binance_klines)
                klines += binance_klines
                self._trim_cache(symbol, interval)
                return klines
        # 2.2. If cache is not empty, and kline[s, e) = cache[s, e)
        elif klines[0].open_time == start_time and klines[-1].open_time == end_time:
            return klines
        # 2.3. If cache is not empty, request kline[s, e) = SQL[s, i) + cache[i, j) + SQL[j, k) + Binance[k, e)
        else:
            # SQL[s, i)
            if klines[0].open_time != start_time:
                s = start_time
                i = s + interval_ms * self.INTERVAL_CACHE_LIMIT[interval]
                sql_klines = self._request_sql_klines(symbol, interval, s, i)
                self._insert_cache(symbol, interval, sql_klines)
                klines = sql_klines + klines
            # SQL[s, i)
            if klines[-1].open_time != end_time:
                j = klines[-1].open_time
                k = (j // interval_ms + 1) * interval_ms
                sql_klines = self._request_sql_klines(symbol, interval, j, k)
                self._insert_cache(symbol, interval, sql_klines)
                klines += sql_klines
            end_time = (klines[0].open_time // interval_ms + 1) * interval_ms
            start_time = (klines[-1].open_time // interval_ms + 1) * interval_ms
            sql_klines = self._request_sql_klines(symbol, interval, start_time, start_time + interval_ms * self.INTERVAL_CACHE_LIMIT[interval])
            self._insert_cache(symbol, interval, sql_klines)
            klines += sql_klines
            start_time = (klines[-1].open_time // interval_ms + 1) * interval_ms
            binance_klines = self._request_binance_klines(symbol, interval, start_time, end_time)
            self._insert_cache(symbol, interval, binance_klines)
            klines += binance_klines
            self._trim_cache(symbol, interval)
            return klines
    