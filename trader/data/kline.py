from .utils import get_key
import redis
import json

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
    return [json.loads(kline) for kline in klines]  # Deserialize each entry

def query_latest_kline(redis: redis.Redis, symbol: str, granular: str) -> dict:
    """Get the latest kline data from Redis

    Args:
        symbol (str): The symbol to get kline data for
        granular (str): The granularity of the kline data

    Returns:
        dict: The latest kline data
    """
    key = get_key(symbol, granular)
    kline = redis.zrevrange(key, 0, 0)
    return json.loads(kline[0]) if kline else {}  # Deserialize the latest entry
