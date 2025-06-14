from .rest import BinanceRestClient
from .websocket import BinanceWebSocketClient
from solvexity.connector.base import ExchangeRestConnector, ExchangeWebSocketConnector
from solvexity.connector.types import OHLCV, OrderBook, Symbol, Trade, Order, OrderStatus, TimeInForce
from typing import List, Dict, Any, Optional
from decimal import Decimal
from solvexity.connector.types import OrderSide, OrderType

class BinanceRestAdapter(ExchangeRestConnector):
    def __init__(self, api_key: str, api_secret: str, use_testnet: bool = False):
        self.rest_client = BinanceRestClient(api_key, api_secret, use_testnet)

    async def __aenter__(self):
        await self.rest_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.rest_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def get_orderbook(self, symbol: Symbol, depth: int = 20) -> OrderBook:
        orderbook = await self.rest_client.get_orderbook(symbol.base_asset + symbol.quote_asset, depth)
        return OrderBook(
            symbol=symbol,
            bids=[(Decimal(bid[0]), Decimal(bid[1])) for bid in orderbook['bids']],
            asks=[(Decimal(ask[0]), Decimal(ask[1])) for ask in orderbook['asks']]
        )
    
    async def get_recent_trades(self, symbol: Symbol, limit: int = 100) -> List[Trade]:
        trades = await self.rest_client.get_recent_trades(symbol.base_asset + symbol.quote_asset, limit)
        return [Trade(
            symbol=symbol,
            price=Decimal(trade[0]),
            quantity=Decimal(trade[1]),
            time=trade[2],
            is_buyer_maker=trade[3],
            is_best_match=trade[4]
        ) for trade in trades]
    
    async def create_order(self, symbol: Symbol, side: OrderSide, order_type: OrderType, quantity: Decimal, price: Optional[Decimal] = None, client_order_id: Optional[str] = None) -> Dict[str, Any]:
        order = await self.rest_client.create_order(symbol.base_asset + symbol.quote_asset, side, order_type, quantity, price, client_order_id)
        return order
    
    async def cancel_order(self, order_id: str, symbol: Symbol) -> Dict[str, Any]:
        order = await self.rest_client.cancel_order(order_id, symbol.base_asset + symbol.quote_asset)
        return order
    
    async def get_open_orders(self, symbol: Symbol) -> List[Order]:
        orders = await self.rest_client.get_open_orders(symbol.base_asset + symbol.quote_asset)
        return [Order(
            symbol=symbol,
            order_id=order['orderId'],
            client_order_id=order['clientOrderId'],
            price=Decimal(order['price']),
            original_quantity=Decimal(order['origQty']),
            executed_quantity=Decimal(order['executedQty']),
            side=OrderSide(order['side']),
            order_type=OrderType(order['type']),
            time_in_force=TimeInForce(order['timeInForce']),
            status=OrderStatus(order['status']),
            timestamp=order['transactTime'],
            update_time=order['updateTime']
        ) for order in orders]
    
    async def get_order_status(self, order_id: str|int, symbol: Symbol) -> Order:
        order = await self.rest_client.get_order_status(order_id, symbol.base_asset + symbol.quote_asset)
        return order
    
    async def get_account_balance(self) -> List[AccountBalance]:
        balance = await self.rest_client.get_account_balance()
        return [AccountBalance(
            asset=balance['asset'],
            free=Decimal(balance['free']),
            locked=Decimal(balance['locked'])
        ) for balance in balance]

class BinanceWebSocketAdapter(ExchangeWebSocketConnector):
    def __init__(self, api_key: str, api_secret: str, use_testnet: bool = False):
        super().__init__(api_key, api_secret, use_testnet)
        self.websocket_client = BinanceWebSocketClient(api_key, api_secret, use_testnet)

    def connect(self):
        self.websocket_client.connect()

    def disconnect(self):
        self.websocket_client.disconnect()
