from typing import Optional
import redis
import json
from .utils import get_key
from .model import KLine
import solvexity.helper.logging as logging 

logger = logging.getLogger("feed")

def query_kline(redis: redis.Redis, symbol: str, granular: str, start_time: int, end_time: int) -> list[KLine]:
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
    return [KLine(**json.loads(kline)) for kline in klines]  # Deserialize each entry

def query_latest_kline(redis: redis.Redis, symbol: str, granular: str) -> Optional[KLine]:
    """Get the latest kline data from Redis

    Args:
        symbol (str): The symbol to get kline data for
        granular (str): The granularity of the kline data

    Returns:
        dict: The latest kline data
    """
    key = get_key(symbol, granular)
    kline = redis.zrevrange(key, 0, 0)
    try:
        if kline and isinstance(kline[0], bytes):
            return KLine(**json.loads(kline[0].decode('utf-8')))  # Deserialize the entry
        else:
            logger.error(f"Unable to get latest kline data: {kline}")
            return None
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.error(f"Failed to deserialize kline: {e}")
        return None


def batch_insert_klines(r: redis.Redis, key: str, historical_klines: list[KLine]):
    """Batch insert pre-created KLine data into Redis.

    Args:
        r (redis.Redis): Redis client instance.
        key (str): The Redis key for storing kline data.
        historical_klines (List[KLine]): List of KLine model instances to insert.
    """
    # Open a pipeline
    with r.pipeline() as pipe:
        for kline in historical_klines:
            score = kline.open_time  # Use open_time as the score
            # Queue the insertion command with JSON serialization
            pipe.zadd(key, {kline.model_dump_json(): score})
        # Execute all commands at once
        pipe.execute()