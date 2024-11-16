from sqlalchemy.engine import Engine
import helper
import pandas as pd
from .model import KLine


def get_klines(engine: Engine, symbol: str, interval: str, start: int, end: int):
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
    df = pd.read_sql(query, engine)
    res = df.values.tolist()
    return [KLine.from_rest(r, interval) for r in res]
