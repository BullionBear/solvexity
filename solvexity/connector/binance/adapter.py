from .rest import BinanceRestClient
from .websocket import BinanceWebSocketClient
from solvexity.connector.base import ExchangeConnector, ExchangeStreamConnector
from solvexity.connector.types import OrderBook, Symbol, Trade, Order, OrderStatus, TimeInForce, AccountBalance, MyTrade, OrderBookUpdate
from typing import List, Dict, Any, Optional, AsyncGenerator
from decimal import Decimal
from solvexity.connector.types import OrderSide, OrderType
from solvexity.logger import SolvexityLogger
from solvexity.connector.exceptions import (
    MarketOrderWithPriceError, InvalidOrderPriceError, OrderIdOrClientOrderIdRequiredError
)
import asyncio

class BinanceRestAdapter(ExchangeConnector):
    def __init__(self, api_key: str, api_secret: str, use_testnet: bool = False):
        self.rest_client = BinanceRestClient(api_key, api_secret, use_testnet)
        self.logger = SolvexityLogger().get_logger(__name__)

    async def __aenter__(self):
        await self.rest_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.rest_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def get_orderbook(self, symbol: Symbol, depth: int = 20) -> OrderBook:
        orderbook = await self.rest_client.get_depth(symbol.base_asset + symbol.quote_asset, depth)
        self.logger.info(f"Orderbook for {symbol.base_asset + symbol.quote_asset}: {orderbook}")
        return OrderBook(
            symbol=symbol,
            last_update_id=orderbook['lastUpdateId'],
            bids=[(Decimal(bid[0]), Decimal(bid[1])) for bid in orderbook['bids']],
            asks=[(Decimal(ask[0]), Decimal(ask[1])) for ask in orderbook['asks']]
        )
    
    async def get_recent_trades(self, symbol: Symbol, limit: int = 100) -> List[Trade]:
        trades = await self.rest_client.get_recent_trades(symbol.base_asset + symbol.quote_asset, limit)
        self.logger.info(f"Recent trades for {symbol.base_asset + symbol.quote_asset}: {trades}")
        side_of_trade = lambda x: OrderSide.SELL if x['isBuyerMaker'] else OrderSide.BUY
        return [Trade(
            id=trade['id'],
            symbol=symbol,
            price=Decimal(trade['price']),
            quantity=Decimal(trade['qty']),
            time=trade['time'],
            side=side_of_trade(trade)
        ) for trade in trades]
    
    async def create_order(self, symbol: Symbol, side: OrderSide, order_type: OrderType, quantity: Decimal, price: Optional[Decimal] = None, time_in_force: Optional[TimeInForce] = None, client_order_id: Optional[str] = None) -> Dict[str, Any]:
        # validate input before sending to rest client
        if order_type == OrderType.MARKET and price is not None:
            raise MarketOrderWithPriceError()
        if order_type == OrderType.LIMIT and price is None:
            raise InvalidOrderPriceError()
        if order_type == OrderType.STOP_LIMIT and price is None:
            raise InvalidOrderPriceError()
        if time_in_force is None:
            time_in_force = TimeInForce.GTC
        
        data = {
            "symbol": symbol.base_asset + symbol.quote_asset,
            "side": side.value,
            "type": order_type.value,
            "quantity": str(quantity),
        }
        
        if price is not None:
            data["price"] = str(price)
        if time_in_force is not None and order_type != OrderType.MARKET:
            data["time_in_force"] = time_in_force.value
        if client_order_id is not None:
            data["client_order_id"] = client_order_id
        order = await self.rest_client.create_order(**data)
        self.logger.info(f"Created order for {symbol.base_asset + symbol.quote_asset}: {order}")
        return order
    
    async def cancel_order(self, symbol: Symbol, order_id: Optional[str] = None, client_order_id: Optional[str] = None) -> Dict[str, Any]:
        if order_id is not None:
            order = await self.rest_client.cancel_order(
                symbol=symbol.base_asset + symbol.quote_asset,
                order_id=int(order_id)
            )
            self.logger.info(f"Cancelled order for {symbol.base_asset + symbol.quote_asset}: {order}")
            return order
        elif client_order_id is not None:
            order = await self.rest_client.cancel_order(
                symbol=symbol.base_asset + symbol.quote_asset,
                orig_client_order_id=client_order_id
            )
            self.logger.info(f"Cancelled order for {symbol.base_asset + symbol.quote_asset}: {order}")
            return order
        else:
            raise OrderIdOrClientOrderIdRequiredError()
    
    async def get_open_orders(self, symbol: Symbol) -> List[Order]:
        orders = await self.rest_client.get_open_orders(symbol.base_asset + symbol.quote_asset)
        self.logger.info(f"Open orders for {symbol.base_asset + symbol.quote_asset}: {orders}")
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

    async def get_order_status(self, symbol: Symbol, order_id: Optional[str] = None, client_order_id: Optional[str] = None) -> Order:
        if order_id is not None:
            order = await self.rest_client.get_order(symbol.base_asset + symbol.quote_asset, order_id=int(order_id))
        elif client_order_id is not None:
            order = await self.rest_client.get_order(symbol.base_asset + symbol.quote_asset, orig_client_order_id=client_order_id)
        else:
            raise OrderIdOrClientOrderIdRequiredError()
            
        self.logger.info(f"Order status for {symbol.base_asset + symbol.quote_asset}: {order}")
        
        # Convert string values to appropriate types
        return Order(
            symbol=symbol,
            order_id=str(order['orderId']),
            client_order_id=order['clientOrderId'],
            price=Decimal(order['price']),
            original_quantity=Decimal(order['origQty']),
            executed_quantity=Decimal(order['executedQty']),
            side=OrderSide(order['side']),
            order_type=OrderType(order['type']),
            time_in_force=TimeInForce(order['timeInForce']),
            status=OrderStatus(order['status']),
            timestamp=order['time'],
            update_time=order['updateTime']
        )
    
    async def get_account_balance(self) -> List[AccountBalance]:
        account_info = await self.rest_client.get_account_information()
        self.logger.debug(f"Account balance: {account_info}")
        return [AccountBalance(
            asset=balance['asset'],
            free=Decimal(balance['free']), 
            locked=Decimal(balance['locked'])
        ) for balance in account_info['balances']]
    
    async def get_my_trades(self, symbol: Symbol, limit: int = 100) -> List[MyTrade]:
        my_trades = await self.rest_client.get_my_trades(symbol.base_asset + symbol.quote_asset, limit=limit)
        self.logger.info(f"My trades for {symbol.base_asset + symbol.quote_asset}: {my_trades}")
        side_of_my_trade = lambda x: OrderSide.BUY if x['isBuyer'] else OrderSide.SELL
        return [MyTrade(
            id=trade['id'],
            symbol=symbol,
            price=Decimal(trade['price']),
            quantity=Decimal(trade['qty']),
            time=trade['time'],
            side=side_of_my_trade(trade),
            is_maker=trade['isMaker'],
            commission=Decimal(trade['commission']),
            commission_asset=trade['commissionAsset'],
        ) for trade in my_trades]
    
    
class BinanceWebSocketAdapter(ExchangeStreamConnector):
    def __init__(self, api_key: str, api_secret: str, use_testnet: bool = False):
        super().__init__(api_key, api_secret, use_testnet)
        self.websocket_client = BinanceWebSocketClient(api_key, api_secret, use_testnet)

    async def __aenter__(self):
        await self.websocket_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.websocket_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def depth_diff_iterator(self, symbol: Symbol) -> AsyncGenerator[OrderBookUpdate, None]:
        queue = asyncio.Queue()
        ws_symbol = (symbol.base_asset + symbol.quote_asset).lower()
        async def orderbook_callback(data: Dict[str, Any]) -> None:
            await queue.put(data)
        
        await self.websocket_client.subscribe_orderbook(
            ws_symbol,
            orderbook_callback
        )
        
        try:
            while True:
                data = await queue.get()
                yield OrderBookUpdate(
                    symbol=symbol,
                    event_time=data['E'],
                    first_update_id=data['U'],
                    last_update_id=data['u'],
                    prev_last_update_id=data['U'],
                    bids=[(Decimal(bid[0]), Decimal(bid[1])) for bid in data['b']],
                    asks=[(Decimal(ask[0]), Decimal(ask[1])) for ask in data['a']]
                )
        finally:
            # Cleanup subscription when generator is closed
            await self.websocket_client.unsubscribe_orderbook(ws_symbol)
    
    async def public_trades_iterator(self, symbol: Symbol) -> AsyncGenerator[Trade, None]:
        queue = asyncio.Queue()
        ws_symbol = (symbol.base_asset + symbol.quote_asset).lower()
        async def trade_callback(data: Dict[str, Any]) -> None:
            await queue.put(data)
        await self.websocket_client.subscribe_trades(ws_symbol, trade_callback)
        
        try:
            while True:
                data = await queue.get()
                yield Trade(
                    id=data['t'], 
                    symbol=symbol,
                    price=Decimal(data['p']),
                    quantity=Decimal(data['q']),
                    time=data['T'],
                    side=OrderSide.BUY if data['m'] else OrderSide.SELL
                )
        finally:
            await self.websocket_client.unsubscribe_trades(ws_symbol)
        
