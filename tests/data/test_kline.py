import pytest
import fakeredis
import json
from trading.data import get_key
from trading.data.kline import query_kline, query_latest_kline

# Fixture to set up and return a fake Redis instance
@pytest.fixture
def redis_client():
    return fakeredis.FakeRedis()

# Sample data fixture
@pytest.fixture
def sample_data():
    return [
        {'t': 1730342940000, 'o': '0.00822100', 'c': '0.00822100', 'h': '0.00822200', 'l': '0.00822100', 'v': '5.96500000'},
        {'t': 1730342960000, 'o': '0.00822500', 'c': '0.00822600', 'h': '0.00822800', 'l': '0.00822500', 'v': '3.21500000'}
    ]

# Helper function to populate Redis with sample data
@pytest.fixture
def populate_redis(redis_client, sample_data):
    key = get_key("BNBBTC", "1m")
    for item in sample_data:
        redis_client.zadd(key, {json.dumps(item): item['t']})
    return key

def test_query_kline(redis_client, sample_data, populate_redis):
    # Define parameters
    symbol = "BNBBTC"
    granular = "1m"
    start_time = 1730342940000
    end_time = 1730342999999

    # Run the function
    result = query_kline(redis_client, symbol, granular, start_time, end_time)

    # Validate result data
    assert result == sample_data

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
    assert result == sample_data[-1]  # Should return the latest kline data

def test_query_latest_kline_no_data(redis_client):
    # Define parameters
    symbol = "BNBBTC"
    granular = "1m"
    
    # Test case with no data
    result = query_latest_kline(redis_client, symbol, granular)
    
    # Validate that result is an empty dictionary when no data exists
    assert result == {}
