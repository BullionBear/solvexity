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
def feed(redis_client):
    return Feed(cache=redis_client)

@pytest.fixture(scope="module")
def no_redis_feed():
    return Feed(cache=None)

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

@pytest.mark.integration
def test_request_local_klines(feed, redis_client):
    # Define test data
    symbol = "BTCUSDT"
    interval = "5m"
    key = f"{symbol}-{interval}"
    
    # Request data first time, it will be stored in cache
    expected_klines = feed._request_local_klines(symbol, interval, 1735113600000, 1735115400000) # 2024, 12, 25, 8:00 - 8:30
    result_klines = feed._request_cache_klines(symbol, interval, 1735113600000, 1735115400000) # 2024, 12, 25, 8:00 - 8:30
    assert len(expected_klines) == 6
    assert len(result_klines) == 6
    for i in range(6):
        assert expected_klines[i].open_time == result_klines[i].open_time

    # Check Redis to verify the data was inserted correctly
    # Request a larger time range to get more data
    expected_klines = feed._request_binance_klines(symbol, interval, 1735113600000, 1735122600000) # 2024, 12, 25, 8:00 - 10:30
    result_klines = feed._request_cache_klines(symbol, interval, 1735113600000, 1735122600000) # 2024, 12, 25, 8:00 - 10:30
    assert len(result_klines) == 30
    for i in range(30):
        assert expected_klines[i].open_time == result_klines[i].open_time
    redis_client.delete(key)

@pytest.mark.integration
def test_request_klines(feed, redis_client):
    symbol = "BTCUSDT"
    interval = "5m"
    key = f"{symbol}-{interval}"
    
    expected_klines = feed._request_local_klines(symbol, interval, 1735113600000, 1735115400000) # 2024, 12, 25, 8:00 - 8:30
    result_klines = feed._request_klines(symbol, interval, 1735113600000, 1735115400000) # 2024, 12, 25, 8:00 - 8:30

    assert len(expected_klines) == 6
    assert len(result_klines) == 6
    redis_client.delete(key)

@pytest.mark.integration
def test_no_redis_request_klines(no_redis_feed):
    symbol = "BTCUSDT"
    interval = "5m"

    # Enable tracking and ensure it's applied
    no_redis_feed.enable_tracking()
    no_redis_feed.tracker.enable()  # Explicitly enable the tracker
    
    # Make the method calls
    result_klines = no_redis_feed._request_klines(symbol, interval, 1735113600000, 1735115400000) # 2024, 12, 25, 8:00 - 8:30
    
    # Verify the results
    assert len(result_klines) == 6

    # Get tracking summary and verify method calls
    summary = no_redis_feed.get_tracking_summary()
    
    # Verify the expected number of calls:
    # _request_klines - called once directly
    assert summary["solvexity.analytic.feed.feed._request_klines"]["calls"] == 1
    # _request_local_klines - called once by _request_klines
    assert summary["solvexity.analytic.feed.feed._request_local_klines"]["calls"] == 1
    # _request_binance_klines - called once when no Redis is available
    assert summary["solvexity.analytic.feed.feed._request_binance_klines"]["calls"] == 1
    
    # Clean up
    no_redis_feed.reset_tracking()
    no_redis_feed.disable_tracking()
    
