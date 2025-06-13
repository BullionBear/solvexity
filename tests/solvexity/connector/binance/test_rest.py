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
async def test_connectivity(connector: BinanceRestConnector):
    """Test basic connectivity to the Binance API."""
    response = await connector.test_connectivity()
    assert isinstance(response, dict)
    assert len(response) == 0  # Empty dict indicates success


@pytest.mark.asyncio
async def test_server_time(connector: BinanceRestConnector):
    """Test getting server time."""
    response = await connector.get_server_time()
    assert isinstance(response, dict)
    assert 'serverTime' in response
    assert isinstance(response['serverTime'], int)


@pytest.mark.asyncio
async def test_exchange_info(connector: BinanceRestConnector):
    """Test getting exchange information."""
    response = await connector.get_exchange_info()
    assert isinstance(response, dict)
    assert 'timezone' in response
    assert 'serverTime' in response
    assert 'symbols' in response
    assert isinstance(response['symbols'], list)
    assert len(response['symbols']) > 0


@pytest.mark.asyncio
async def test_order_book_depth(connector: BinanceRestConnector):
    """Test getting order book depth."""
    symbol = 'BTCUSDT'
    response = await connector.get_depth(symbol)
    assert isinstance(response, dict)
    assert 'lastUpdateId' in response
    assert 'bids' in response
    assert 'asks' in response
    assert isinstance(response['bids'], list)
    assert isinstance(response['asks'], list)


@pytest.mark.asyncio
async def test_klines(connector: BinanceRestConnector):
    """Test getting klines/candlestick data."""
    symbol = 'BTCUSDT'
    interval = '1h'
    response = await connector.get_klines(symbol, interval, limit=10)
    assert isinstance(response, list)
    assert len(response) <= 10
    if len(response) > 0:
        # Each kline contains: [Open time, Open, High, Low, Close, Volume, Close time, Quote asset volume, Number of trades, Taker buy base asset volume, Taker buy quote asset volume, Ignore]
        assert len(response[0]) == 12
        # Verify the first element is a timestamp
        assert isinstance(response[0][0], int)
        # Verify price fields are strings
        assert isinstance(response[0][1], str)  # Open price
        assert isinstance(response[0][2], str)  # High price
        assert isinstance(response[0][3], str)  # Low price
        assert isinstance(response[0][4], str)  # Close price


@pytest.mark.asyncio
async def test_get_account_information(connector: BinanceRestConnector):
    """Test fetching account information (requires API key/secret)."""
    info = await connector.get_account_information()
    assert isinstance(info, dict)
    assert 'balances' in info
    assert 'accountType' in info


@pytest.mark.asyncio
async def test_create_and_cancel_market_order(connector: BinanceRestConnector):
    """Test creating, fetching, and canceling a market order (testnet)."""
    symbol = 'BTCUSDT'
    # Use a very small quantity for testnet
    quantity = 0.0001
    # Create a market BUY order
    order = await connector.create_order(
        symbol=symbol,
        side='BUY',
        type='MARKET',
        quantity=quantity
    )
    assert 'orderId' in order
    order_id = order['orderId']
    # Fetch the order
    fetched = await connector.get_order(symbol=symbol, order_id=order_id)
    assert fetched['orderId'] == order_id
    assert fetched['symbol'] == symbol
    # Cancel the order (if not filled)
    if fetched['status'] not in ('FILLED', 'CANCELED', 'EXPIRED'):
        cancel = await connector.cancel_order(symbol=symbol, order_id=order_id)
        assert cancel['orderId'] == order_id


@pytest.mark.asyncio
async def test_get_open_orders(connector: BinanceRestConnector):
    """Test listing open orders (requires API key/secret)."""
    symbol = 'BTCUSDT'
    open_orders = await connector.get_open_orders(symbol=symbol)
    assert isinstance(open_orders, list)
    for order in open_orders:
        assert order['symbol'] == symbol
        assert 'orderId' in order


@pytest.mark.asyncio
async def test_get_my_trades(connector: BinanceRestConnector):
    """Test listing user trades (requires API key/secret)."""
    symbol = 'BTCUSDT'
    trades = await connector.get_my_trades(symbol=symbol, limit=5)
    assert isinstance(trades, list)
    for trade in trades:
        assert trade['symbol'] == symbol
        assert 'id' in trade

