import redis
import binance
import pandas as pd
from sqlalchemy.engine import Engine

from .model import KLine
from solvexity.helper import to_ms_interval


class Feed:
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

    def _insert_cache(self, symbol: str, interval: str, klines: list[KLine]):
        key = f"{symbol}-{interval}"
        self.redis.set(key, klines)

    def get_klines(self, symbol: str, interval: str, limit: int):
        pass