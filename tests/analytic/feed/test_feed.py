import pytest
from unittest.mock import MagicMock
from solvexity.analytic.feed import Feed


@pytest.fixture
def mock_feed():
    mock_redis = MagicMock()
    return Feed(cache=mock_redis)


def test_get_cache_key(mock_feed):
    symbol = "BTCUSDT"
    interval = "1m"
    expected = "BTCUSDT-1m"
    actual = mock_feed._get_cache_key(symbol, interval)
    assert actual == expected