import os
import pytest
import redis
import sqlalchemy
from solvexity.analytic.feed import Feed
from solvexity.analytic.model import KLine  # Ensure your KLine has .from_binance() classmethod
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture(scope="module")
def redis_client():
    r = redis.Redis(host='localhost', port=6379, db=0)  # Use a test Redis instance
    yield r
    r.flushdb()  # Clean up after test

@pytest.fixture(scope="module")
def sql_engine():
    sql_url = os.getenv("SQL_URL")
    engine = sqlalchemy.create_engine(sql_url)
    yield engine
    engine.dispose()

@pytest.fixture(scope="module")
def feed(redis_client, sql_engine):
    return Feed(cache=redis_client, sql_engine=sql_engine)

@pytest.mark.integration
def test_request_binance_klines(feed):
    symbol = "BTCUSDT"
    interval = "1m"
    start = int(datetime(year=2025, month=1, day=5, hour=9, minute=0, second=0, tzinfo=timezone.utc).timestamp() * 1000)
    end = int(datetime(year=2025, month=1, day=5, hour=9, minute=30, second=0, tzinfo=timezone.utc).timestamp() * 1000)
    

    klines = feed._request_binance_klines(symbol, interval, start, end)

    assert isinstance(klines, list)
    assert len(klines) > 0
    assert isinstance(klines[0], KLine)
    assert hasattr(klines[0], "open_time")  # Assuming your KLine has such a field