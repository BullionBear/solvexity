from .rest import BinanceRestClient
from .websocket import BinanceWebSocketClient
from solvexity.connector.base import ExchangeRestConnector, ExchangeWebSocketConnector
from solvexity.connector.types import OHLCV, OrderBook, Symbol, Trade
from typing import List
from decimal import Decimal

class BinanceRestAdapter(ExchangeRestConnector):
    def __init__(self, api_key: str, api_secret: str, use_testnet: bool = False):
        self.rest_client = BinanceRestClient(api_key, api_secret, use_testnet)

    async def __aenter__(self):
        await self.rest_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.rest_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def get_ohlcv(self, symbol: Symbol, interval: str, limit: int = 100) -> List[OHLCV]:
        ohlcvs = await self.rest_client.get_ohlcv(symbol.base_asset + symbol.quote_asset, interval, limit)
        return [OHLCV(
            symbol=symbol,
            open_time=ohlcv[0],
            open=Decimal(ohlcv[1]),
            high=Decimal(ohlcv[2]),
            low=Decimal(ohlcv[3]),
            close=Decimal(ohlcv[4]),
            volume=Decimal(ohlcv[5]),
            close_time=ohlcv[6],
            quote_volume=Decimal(ohlcv[7]),
            n_trades=ohlcv[8],
            taker_buy_base_asset_volume=Decimal(ohlcv[9]),
            taker_buy_quote_asset_volume=Decimal(ohlcv[10]),
            ignore=ohlcv[11]
        ) for ohlcv in ohlcvs]
    
    async def get_orderbook(self, symbol: Symbol, depth: int = 20) -> OrderBook:
        return await self.rest_client.get_orderbook(symbol.base_asset + symbol.quote_asset, depth)
    
    async def get_trades(self, symbol: Symbol, limit: int = 100) -> List[Trade]:


class BinanceWebSocketAdapter(ExchangeWebSocketConnector):
    def __init__(self, api_key: str, api_secret: str, use_testnet: bool = False):
        super().__init__(api_key, api_secret, use_testnet)
        self.websocket_client = BinanceWebSocketClient(api_key, api_secret, use_testnet)

    def connect(self):
        self.websocket_client.connect()

    def disconnect(self):
        self.websocket_client.disconnect()
