import pytest
import redis
import sqlalchemy
from binance import Client as BinanceClient
from solvexity.analytic.feed import Feed
from solvexity.analytic.model import KLine  # Ensure your KLine has .from_binance() classmethod
from solvexity.helper import to_ms_interval
from datetime import datetime, timedelta

@pytest.fixture(scope="module")
def redis_client():
    r = redis.Redis(host='localhost', port=6379, db=0)  # Use a test Redis instance
    yield r
    r.flushdb()  # Clean up after test

@pytest.fixture(scope="module")
def sql_engine():
    # Use a local or Docker-based test DB; this example uses SQLite in-memory for simplicity
    engine = sqlalchemy.create_engine("sqlite:///:memory:")
    yield engine
    engine.dispose()

@pytest.fixture(scope="module")
def feed(redis_client, sql_engine):
    return Feed(cache=redis_client, sql_engine=sql_engine)

@pytest.mark.integration
def test_request_binance_klines(feed):
    symbol = "BTCUSDT"
    interval = "1m"
    now = int(datetime.now().timestamp() * 1000)
    five_minutes_ago = now - 5 * 60 * 1000

    klines = feed._request_binance_klines(symbol, interval, five_minutes_ago, now)

    assert isinstance(klines, list)
    assert len(klines) > 0
    assert isinstance(klines[0], KLine)
    assert hasattr(klines[0], "open_time")  # Assuming your KLine has such a field