import pandas as pd
from .utils import get_key
import redis

def query_kline(redis: redis.Redis, symbol: str, granular: str, start_time: int, end_time: int) -> list[dict]:
    """Get kline data from Redis

    Args:
        symbol (str): The symbol to get kline data for
        granular (str): The granularity of the kline data
        start_time (int): The start time of the kline data
        end_time (int): The end time of the kline data

    Returns:
        list[dict]: The kline data
    """
    key = get_key(symbol, granular)
    klines = redis.zrangebyscore(key, start_time, end_time)
    return klines

 
if __name__ == "__main__":
    import time
    r = redis.Redis(host="localhost", port=6379, db=0)
    end_time = int(time.time() * 1000)
    start_time = end_time - 60000
    klines = query_kline(r, "BTCUSDT", "1m", start_time=start_time, end_time=end_time)
    df = pd.DataFrame(klines)
    print(df)