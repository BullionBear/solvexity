import pytest
import os
from typing import Dict, Any
from solvexity.connector.binance.rest import BinanceRestConnector
import aiohttp


@pytest.fixture
def api_credentials() -> Dict[str, str]:
    """Get API credentials from environment variables."""
    return {
        'api_key': os.getenv('BINANCE_API_KEY', ''),
        'api_secret': os.getenv('BINANCE_API_SECRET', '')
    }


@pytest.fixture
async def connector(api_credentials: Dict[str, str]):
    """Create a test connector instance."""
    connector = BinanceRestConnector(
        api_key=api_credentials['api_key'],
        api_secret=api_credentials['api_secret'],
        use_testnet=True  # Always use testnet for tests
    )
    async with connector:
        yield connector


@pytest.mark.asyncio
async def test_get_ticker_24hr(connector: BinanceRestConnector):
    """Test getting 24hr ticker information."""
    # Test with a known trading pair
    response = await connector.get_ticker_24hr('BTCUSDT')
    
    # Verify response structure
    assert isinstance(response, dict)
    assert 'symbol' in response
    assert 'lastPrice' in response
    assert 'volume' in response
    assert response['symbol'] == 'BTCUSDT'
    
    # Verify numeric fields
    assert float(response['lastPrice']) > 0
    assert float(response['volume']) >= 0


@pytest.mark.asyncio
async def test_get_depth(connector: BinanceRestConnector):
    """Test getting order book depth."""
    # Test with a known trading pair
    response = await connector.get_depth('BTCUSDT', limit=5)
    
    # Verify response structure
    assert isinstance(response, dict)
    assert 'bids' in response
    assert 'asks' in response
    assert len(response['bids']) <= 5
    assert len(response['asks']) <= 5
    
    # Verify bid/ask structure
    if response['bids']:
        bid = response['bids'][0]
        assert len(bid) == 2
        assert float(bid[0]) > 0  # price
        assert float(bid[1]) > 0  # quantity


@pytest.mark.asyncio
async def test_get_trades(connector: BinanceRestConnector):
    """Test getting recent trades."""
    # Test with a known trading pair
    response = await connector.get_trades('BTCUSDT', limit=5)
    
    # Verify response structure
    assert isinstance(response, list)
    assert len(response) <= 5
    
    if response:
        trade = response[0]
        assert 'id' in trade
        assert 'price' in trade
        assert 'qty' in trade
        assert 'time' in trade
        assert float(trade['price']) > 0
        assert float(trade['qty']) > 0


@pytest.mark.asyncio
async def test_create_and_cancel_order(connector: BinanceRestConnector):
    """Test creating and canceling an order."""
    # Skip if no API credentials
    if not connector.api_key or not connector.api_secret:
        pytest.skip("No API credentials provided")
        
    # Create a limit order
    order = await connector.create_order(
        symbol='BTCUSDT',
        side='BUY',
        order_type='LIMIT',
        quantity=0.001,  # Minimum order size
        price=10000,  # Far from current price to avoid execution
        time_in_force='GTC'
    )
    
    # Verify order creation
    assert isinstance(order, dict)
    assert 'orderId' in order
    assert order['symbol'] == 'BTCUSDT'
    assert order['side'] == 'BUY'
    assert order['type'] == 'LIMIT'
    
    # Cancel the order
    cancel_response = await connector.cancel_order(
        symbol='BTCUSDT',
        order_id=order['orderId']
    )
    
    # Verify order cancellation
    assert isinstance(cancel_response, dict)
    assert cancel_response['orderId'] == order['orderId']
    assert cancel_response['status'] == 'CANCELED'


@pytest.mark.asyncio
async def test_get_order(connector: BinanceRestConnector):
    """Test getting order information."""
    # Skip if no API credentials
    if not connector.api_key or not connector.api_secret:
        pytest.skip("No API credentials provided")
        
    # Create a test order
    order = await connector.create_order(
        symbol='BTCUSDT',
        side='BUY',
        order_type='LIMIT',
        quantity=0.001,
        price=10000,
        time_in_force='GTC'
    )
    
    try:
        # Get order information
        order_info = await connector.get_order(
            symbol='BTCUSDT',
            order_id=order['orderId']
        )
        
        # Verify order information
        assert isinstance(order_info, dict)
        assert order_info['orderId'] == order['orderId']
        assert order_info['symbol'] == 'BTCUSDT'
        assert order_info['side'] == 'BUY'
        assert order_info['type'] == 'LIMIT'
        
    finally:
        # Clean up: cancel the order
        await connector.cancel_order(
            symbol='BTCUSDT',
            order_id=order['orderId']
        )


@pytest.mark.asyncio
async def test_get_account(connector: BinanceRestConnector):
    """Test getting account information."""
    # Skip if no API credentials
    if not connector.api_key or not connector.api_secret:
        pytest.skip("No API credentials provided")
        
    response = await connector.get_account()
    
    # Verify response structure
    assert isinstance(response, dict)
    assert 'balances' in response
    assert 'permissions' in response
    
    # Verify balance structure
    if response['balances']:
        balance = response['balances'][0]
        assert 'asset' in balance
        assert 'free' in balance
        assert 'locked' in balance
        assert float(balance['free']) >= 0
        assert float(balance['locked']) >= 0


@pytest.mark.asyncio
async def test_error_handling(connector: BinanceRestConnector):
    """Test error handling for invalid requests."""
    # Test with invalid symbol
    with pytest.raises(aiohttp.ClientResponseError) as exc_info:
        await connector.get_ticker_24hr('INVALID_SYMBOL')
    assert exc_info.value.status == 400
    
    # Test with invalid order parameters
    with pytest.raises(aiohttp.ClientResponseError) as exc_info:
        await connector.create_order(
            symbol='BTCUSDT',
            side='INVALID_SIDE',
            order_type='LIMIT',
            quantity=0.001,
            price=10000
        )
    assert exc_info.value.status == 400 