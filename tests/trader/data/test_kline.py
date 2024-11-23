import pytest
import fakeredis
import json
from trader.data import get_key
from trader.data.kline import query_kline, query_latest_kline
from trader.data.model import KLine

# Fixture to set up and return a fake Redis instance
@pytest.fixture
def redis_client():
    return fakeredis.FakeRedis()

# Sample data fixture
@pytest.fixture
def sample_data():
    return [
        {
            "interval": "1m",
            "open_time": 1730342940000,
            "close_time": 1730342945999,
            "event_time": 1730342941000,  # Add this field
            "open": 0.00822100,
            "close": 0.00822100,
            "high": 0.00822200,
            "low": 0.00822100,
            "number_of_trades": 1,
            "base_asset_volume": 5.965,
            "quote_asset_volume": 0.049,
            "taker_buy_base_asset_volume": 2.5,
            "taker_buy_quote_asset_volume": 0.025,
            "is_closed": True,
        },
        {
            "interval": "1m",
            "open_time": 1730342960000,
            "close_time": 1730342965999,
            "event_time": 1730342961000,  # Add this field
            "open": 0.00822500,
            "close": 0.00822600,
            "high": 0.00822800,
            "low": 0.00822500,
            "number_of_trades": 2,
            "base_asset_volume": 3.215,
            "quote_asset_volume": 0.027,
            "taker_buy_base_asset_volume": 1.6,
            "taker_buy_quote_asset_volume": 0.014,
            "is_closed": True,
        },
    ]


# Helper function to populate Redis with sample data
@pytest.fixture
def populate_redis(redis_client, sample_data):
    key = get_key("BNBBTC", "1m")
    for item in sample_data:
        # Serialize each KLine data as JSON
        redis_client.zadd(key, {json.dumps(item): item["open_time"]})
    return key

def test_query_kline(redis_client, sample_data, populate_redis):
    # Define parameters
    symbol = "BNBBTC"
    granular = "1m"
    start_time = 1730342940000
    end_time = 1730342999999

    # Run the function
    result = query_kline(redis_client, symbol, granular, start_time, end_time)

    # Convert sample data to list of KLine instances for comparison
    expected_result = [KLine(**item) for item in sample_data]

    # Validate result data
    assert result == expected_result

def test_query_kline_no_data(redis_client, populate_redis):
    # Clear Redis data
    redis_client.delete(populate_redis)

    # Define parameters
    symbol = "BNBBTC"
    granular = "1m"
    start_time = 1730342940000
    end_time = 1730342999999

    # Run the function
    result = query_kline(redis_client, symbol, granular, start_time, end_time)

    # Validate that result is an empty list
    assert result == []

def test_query_latest_kline(redis_client, sample_data, populate_redis):
    # Define parameters
    symbol = "BNBBTC"
    granular = "1m"
    
    # Test case with data available
    result = query_latest_kline(redis_client, symbol, granular)

    # Validate result matches the latest kline data as KLine instance
    expected_latest = KLine(**sample_data[-1])
    assert result == expected_latest

def test_query_latest_kline_no_data(redis_client):
    # Define parameters
    symbol = "BNBBTC"
    granular = "1m"
    
    # Test case with no data
    result = query_latest_kline(redis_client, symbol, granular)
    
    # Validate that result is None when no data exists
    assert result is None
