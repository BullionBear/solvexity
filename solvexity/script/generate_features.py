import os
import pandas as pd
import datetime as dt
from redis import Redis
from sqlalchemy import create_engine
from solvexity.helper import to_ms_interval
from solvexity.analytic.feed import Feed
from solvexity.analytic.pattern import Pattern

from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    redis_client = Redis(host='localhost', port=6379, db=0)
    sql_engine = create_engine(os.getenv("SQL_URL"))
    feed = Feed(redis_client, sql_engine)
    pattern = Pattern(feed)
    symbol = "BTCUSDT"
    lookbacks = [("1m", 30), ("1m", 180), ("5m", 30), ("5m", 180), ("15m", 30), ("15m", 180), ("1h", 30), ("1h", 180)] # , ("4h", 30), ("4h", 180), ("1d", 30)]
    lookafters = [("1m", 60), ("1m", 60 * 24)]
    start_time = dt.datetime(2022, 3, 1, 0, 0, 0, tzinfo=dt.timezone.utc) # span end time
    end_time = dt.datetime(2025, 3, 29, 0, 0, 0, tzinfo=dt.timezone.utc)
    step_size = dt.timedelta(days=1)
    records = []
    while start_time < end_time:
        record = {"timestamp": int(start_time.timestamp() * 1000)}
        print(f"Processing {start_time}")
        for interval, lookback in lookbacks:
            print(f"Calculating features for {interval} interval with lookback {lookback}")
            span_end_time = int(start_time.timestamp() * 1000)
            span_start_time = int(span_end_time - to_ms_interval(interval) * lookback)
            record[f"returns_{interval}_{lookback}"] = pattern.calc_returns(symbol, interval, span_start_time, span_end_time)
            record[f"volatility_{interval}_{lookback}"] = pattern.calc_volatility(symbol, interval, span_start_time, span_end_time)
            record[f"mdd_{interval}_{lookback}"] = pattern.calc_mdd(symbol, interval, span_start_time, span_end_time)
            record[f"skewness_{interval}_{lookback}"] = pattern.calc_skewness(symbol, interval, span_start_time, span_end_time)
            record[f"kurtosis_{interval}_{lookback}"] = pattern.calc_kurtosis(symbol, interval, span_start_time, span_end_time)
            # egarch = pattern.calc_egarch(symbol, interval, span_start_time, span_end_time)
            # for key, value in egarch.items():
            #     record[f"{key}_{interval}_{lookback}"] = value
        # Result for the current step
        for interval, lookafter in lookafters:
            span_start_time = int(start_time.timestamp() * 1000)
            span_end_time = int(span_start_time + to_ms_interval(interval) * lookafter)
            record[f"stopping_returns_{interval}_{lookafter}"] = pattern.stopping_return(symbol, interval, span_start_time, span_end_time, -0.03, 0.06)
            
        records.append(record)
        start_time += step_size
    df = pd.DataFrame(records)
    df.to_csv("features.csv", index=False)