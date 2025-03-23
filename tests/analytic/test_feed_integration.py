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
    assert len(klines) == 30
    assert isinstance(klines[0], KLine)
    assert hasattr(klines[0], "open_time")  # Assuming your KLine has such a field

@pytest.mark.integration
def test_request_sql_klines(feed):
    symbol = "BTCUSDT"
    interval = "1m"
    start = int(datetime(year=2025, month=1, day=5, hour=9, minute=0, second=0, tzinfo=timezone.utc).timestamp() * 1000)
    end = int(datetime(year=2025, month=1, day=5, hour=9, minute=30, second=0, tzinfo=timezone.utc).timestamp() * 1000)
    

    klines = feed._request_sql_klines(symbol, interval, start, end)

    assert isinstance(klines, list)
    assert len(klines) == 30
    assert isinstance(klines[0], KLine)
    assert hasattr(klines[0], "open_time")  # Assuming your KLine has such a field

@pytest.mark.integration
def test_request_sql_klines_5m(feed):
    symbol = "BTCUSDT"
    interval = "5m"
    start = int(datetime(year=2025, month=1, day=5, hour=9, minute=0, second=0, tzinfo=timezone.utc).timestamp() * 1000)
    end = int(datetime(year=2025, month=1, day=5, hour=9, minute=30, second=0, tzinfo=timezone.utc).timestamp() * 1000)
    

    klines = feed._request_sql_klines(symbol, interval, start, end)

    assert isinstance(klines, list)
    assert len(klines) == 6
    assert isinstance(klines[0], KLine)
    assert hasattr(klines[0], "open_time")  # Assuming your KLine has such a field

@pytest.mark.integration
def test_insert_cache(feed, redis_client):
    # Define test data
    symbol = "BTCUSDT"
    interval = "1m"
    klines = [
        KLine.from_binance([
            1672502400000,  # open_time
            "16500.0",      # open_px
            "16550.0",      # high_px
            "16450.0",      # low_px
            "16520.0",      # close_px
            "100.0",        # base_asset_volume
            1672502460000,  # close_time
            "1650000.0",    # quote_asset_volume
            100,            # number_of_trades
            "50.0",         # taker_buy_base_asset_volume
            "825000.0",     # taker_buy_quote_asset_volume
            "0"             # unused_field
        ], symbol, interval),
        KLine.from_binance([
            1672502460000,  # open_time
            "16520.0",       # open_px
            "16570.0",       # high_px
            "16470.0",       # low_px
            "16540.0",       # close_px
            "120.0",         # base_asset_volume
            1672502520000,   # close_time
            "1980000.0",     # quote_asset_volume
            120,             # number_of_trades
            "60.0",          # taker_buy_base_asset_volume
            "990000.0",      # taker_buy_quote_asset_volume
            "0"             # unused_field
        ], symbol, interval),
    ]

    # Insert data into Redis
    inserted_count = feed._insert_cache(symbol, interval, klines)

    # Verify the insertion
    assert inserted_count == len(klines)  # Ensure all klines were inserted

    # Check Redis to verify the data was inserted correctly
    cache_key = feed._get_cache_key(symbol, interval)
    for kline in klines:
        # Verify that each kline exists in the Redis zset with the correct score
        assert redis_client.zrangebyscore(cache_key, kline.open_time, kline.open_time, withscores=True) == [(kline.model_dump_json().encode(), kline.open_time)]

    # Clean up Redis after the test
    redis_client.delete(cache_key)


@pytest.mark.integration
def test_request_cache_klines(feed, redis_client):
    # Define test data
    symbol = "BTCUSDT"
    interval = "1m"
    key = f"{symbol}-{interval}"

    # Create sample KLine data
    expected_klines = [
        KLine.from_binance([
            1672502400000,  # open_time
            "16500.0",      # open_px
            "16550.0",      # high_px
            "16450.0",      # low_px
            "16520.0",      # close_px
            "100.0",        # base_asset_volume
            1672502460000,  # close_time
            "1650000.0",    # quote_asset_volume
            100,            # number_of_trades
            "50.0",         # taker_buy_base_asset_volume
            "825000.0",     # taker_buy_quote_asset_volume
            "0"             # unused_field
        ], symbol, interval),
        KLine.from_binance([
            1672502460000,  # open_time
            "16520.0",       # open_px
            "16570.0",       # high_px
            "16470.0",       # low_px
            "16540.0",       # close_px
            "120.0",         # base_asset_volume
            1672502520000,   # close_time
            "1980000.0",     # quote_asset_volume
            120,             # number_of_trades
            "60.0",          # taker_buy_base_asset_volume
            "990000.0",      # taker_buy_quote_asset_volume
            "0"             # unused_field
        ], symbol, interval),
    ]

    # Insert test data into Redis
    redis_client.zadd(key, {expected_klines[0].model_dump_json(): expected_klines[0].open_time})
    redis_client.zadd(key, {expected_klines[1].model_dump_json(): expected_klines[1].open_time})

    # Query the cache
    start_time = 1672502400000
    end_time = 1672502520000
    klines = feed._request_cache_klines(symbol, interval, start_time, end_time)

    # Verify the results
    assert isinstance(klines, list)
    assert len(klines) == 2
    assert isinstance(klines[0], KLine)
    assert klines[0].open_time == expected_klines[0].open_time
    assert klines[1].open_time == expected_klines[1].open_time

    # Clean up Redis
    redis_client.delete(key)