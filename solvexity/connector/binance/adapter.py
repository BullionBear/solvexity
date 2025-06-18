import asyncio
from decimal import Decimal
from typing import Any, AsyncGenerator, Dict, List, Optional

from aiocache import cached
from cachetools import TTLCache

from solvexity.connector.base import ExchangeConnector, ExchangeStreamConnector
from solvexity.connector.exceptions import (
    InvalidOrderPriceError, MarketOrderWithPriceError,
    OrderIdOrClientOrderIdRequiredError)
from solvexity.connector.types import (AccountBalance, InstrumentType, MyTrade,
                                       Order, OrderBook, OrderBookUpdate,
                                       OrderSide, OrderStatus, OrderType,
                                       Symbol, TimeInForce, Trade)
from solvexity.logger import SolvexityLogger

from .rest import BinanceRestClient
from .websocket import BinanceWebSocketClient


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
        orderbook = await self.rest_client.get_depth(
            symbol.base_currency + symbol.quote_currency, depth
        )
        self.logger.info(
            f"Orderbook for {symbol.base_currency + symbol.quote_currency}: {orderbook}"
        )
        return OrderBook(
            symbol=symbol,
            last_update_id=orderbook["lastUpdateId"],
            bids=[(Decimal(bid[0]), Decimal(bid[1])) for bid in orderbook["bids"]],
            asks=[(Decimal(ask[0]), Decimal(ask[1])) for ask in orderbook["asks"]],
        )

    async def get_recent_trades(self, symbol: Symbol, limit: int = 100) -> List[Trade]:
        trades = await self.rest_client.get_recent_trades(
            symbol.base_currency + symbol.quote_currency, limit
        )
        self.logger.info(
            f"Recent trades for {symbol.base_currency + symbol.quote_currency}: {trades}"
        )
        return [
            Trade(
                id=trade["id"],
                symbol=symbol,
                price=Decimal(trade["price"]),
                quantity=Decimal(trade["qty"]),
                time=trade["time"],
                side=self.determine_side(trade),
            )
            for trade in trades
        ]

    def determine_side(self, trade: Dict[str, Any]) -> OrderSide:
        return OrderSide.SELL if trade["isBuyerMaker"] else OrderSide.BUY

    async def create_order(
        self,
        symbol: Symbol,
        side: OrderSide,
        order_type: OrderType,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        time_in_force: Optional[TimeInForce] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
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
            "symbol": symbol.base_currency + symbol.quote_currency,
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
        self.logger.info(
            f"Created order for {symbol.base_currency + symbol.quote_currency}: {order}"
        )
        return order

    async def cancel_order(
        self,
        symbol: Symbol,
        order_id: Optional[str] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if order_id is not None:
            order = await self.rest_client.cancel_order(
                symbol=symbol.base_currency + symbol.quote_currency, order_id=int(order_id)
            )
            self.logger.info(
                f"Cancelled order for {symbol.base_currency + symbol.quote_currency}: {order}"
            )
            return order
        elif client_order_id is not None:
            order = await self.rest_client.cancel_order(
                symbol=symbol.base_currency + symbol.quote_currency,
                orig_client_order_id=client_order_id,
            )
            self.logger.info(
                f"Cancelled order for {symbol.base_currency + symbol.quote_currency}: {order}"
            )
            return order
        else:
            raise OrderIdOrClientOrderIdRequiredError()

    async def get_open_orders(self, symbol: Symbol) -> List[Order]:
        orders = await self.rest_client.get_open_orders(
            symbol.base_currency + symbol.quote_currency
        )
        self.logger.info(
            f"Open orders for {symbol.base_currency + symbol.quote_currency}: {orders}"
        )
        return [
            Order(
                symbol=symbol,
                order_id=order["orderId"],
                client_order_id=order["clientOrderId"],
                price=Decimal(order["price"]),
                original_quantity=Decimal(order["origQty"]),
                executed_quantity=Decimal(order["executedQty"]),
                side=OrderSide(order["side"]),
                order_type=OrderType(order["type"]),
                time_in_force=TimeInForce(order["timeInForce"]),
                status=OrderStatus(order["status"]),
                timestamp=order["transactTime"],
                update_time=order["updateTime"],
            )
            for order in orders
        ]

    async def get_order_status(
        self,
        symbol: Symbol,
        order_id: Optional[str] = None,
        client_order_id: Optional[str] = None,
    ) -> Order:
        if order_id is not None:
            order = await self.rest_client.get_order(
                symbol.base_currency + symbol.quote_currency, order_id=int(order_id)
            )
        elif client_order_id is not None:
            order = await self.rest_client.get_order(
                symbol.base_currency + symbol.quote_currency,
                orig_client_order_id=client_order_id,
            )
        else:
            raise OrderIdOrClientOrderIdRequiredError()

        self.logger.info(
            f"Order status for {symbol.base_currency + symbol.quote_currency}: {order}"
        )

        # Convert string values to appropriate types
        return Order(
            symbol=symbol,
            order_id=str(order["orderId"]),
            client_order_id=order["clientOrderId"],
            price=Decimal(order["price"]),
            original_quantity=Decimal(order["origQty"]),
            executed_quantity=Decimal(order["executedQty"]),
            side=OrderSide(order["side"]),
            order_type=OrderType(order["type"]),
            time_in_force=TimeInForce(order["timeInForce"]),
            status=OrderStatus(order["status"]),
            timestamp=order["time"],
            update_time=order["updateTime"],
        )

    async def get_account_balance(self) -> List[AccountBalance]:
        account_info = await self.rest_client.get_account_information()
        self.logger.debug(f"Account balance: {account_info}")
        return [
            AccountBalance(
                asset=balance["asset"],
                free=Decimal(balance["free"]),
                locked=Decimal(balance["locked"]),
            )
            for balance in account_info["balances"]
        ]

    async def get_my_trades(self, symbol: Symbol, limit: int = 100) -> List[MyTrade]:
        my_trades = await self.rest_client.get_my_trades(
            symbol.base_currency + symbol.quote_currency, limit=limit
        )
        self.logger.info(
            f"My trades for {symbol.base_currency + symbol.quote_currency}: {my_trades}"
        )
        return [
            MyTrade(
                id=trade["id"],
                order_id=trade["orderId"],
                symbol=symbol,
                price=Decimal(trade["price"]),
                quantity=Decimal(trade["qty"]),
                time=trade["time"],
                side=self.determine_side(trade),
                is_maker=trade["isMaker"],
                commission=Decimal(trade["commission"]),
                commission_asset=trade["commissionAsset"],
            )
            for trade in my_trades
        ]


class BinanceWebSocketAdapter(ExchangeStreamConnector):
    _exchange_info_cache = TTLCache(
        maxsize=5, ttl=3600
    )  # Stores multiple exchange responses

    def __init__(self, api_key: str, api_secret: str, use_testnet: bool = False):
        self.websocket_client = BinanceWebSocketClient(api_key, api_secret, use_testnet)
        self.logger = SolvexityLogger().get_logger(__name__)
        # user data stream fields
        self.is_user_data_stream_subscribed = False
        self.user_data_queue = {
            "trade": asyncio.Queue(),
            "order": asyncio.Queue(),
            "account": asyncio.Queue(),
        }
        self.is_trade_stream_subscribed = False
        self.is_order_stream_subscribed = False
        self.is_account_stream_subscribed = False

    async def __aenter__(self):
        await self.websocket_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.websocket_client.__aexit__(exc_type, exc_val, exc_tb)

    async def depth_diff_iterator(
        self, symbol: Symbol
    ) -> AsyncGenerator[OrderBookUpdate, None]:
        queue = asyncio.Queue()
        ws_symbol = (symbol.base_currency + symbol.quote_currency).lower()

        async def orderbook_callback(data: Dict[str, Any]) -> None:
            await queue.put(data)

        await self.websocket_client.subscribe_orderbook(ws_symbol, orderbook_callback)

        try:
            while True:
                data = await queue.get()
                yield OrderBookUpdate(
                    symbol=symbol,
                    event_time=data["E"],
                    first_update_id=data["U"],
                    last_update_id=data["u"],
                    prev_last_update_id=data["U"],
                    bids=[(Decimal(bid[0]), Decimal(bid[1])) for bid in data["b"]],
                    asks=[(Decimal(ask[0]), Decimal(ask[1])) for ask in data["a"]],
                )
        finally:
            # Cleanup subscription when generator is closed
            await self.websocket_client.unsubscribe_orderbook(ws_symbol)

    async def public_trades_iterator(
        self, symbol: Symbol
    ) -> AsyncGenerator[Trade, None]:
        queue = asyncio.Queue()
        ws_symbol = (symbol.base_currency + symbol.quote_currency).lower()

        async def trade_callback(data: Dict[str, Any]) -> None:
            await queue.put(data)

        await self.websocket_client.subscribe_trades(ws_symbol, trade_callback)

        try:
            while True:
                data = await queue.get()
                yield Trade(
                    id=data["t"],
                    symbol=symbol,
                    price=Decimal(data["p"]),
                    quantity=Decimal(data["q"]),
                    time=data["T"],
                    side=self.determine_side(data),
                )
        finally:
            await self.websocket_client.unsubscribe_trades(ws_symbol)

    def determine_side(self, data: Dict[str, Any]) -> OrderSide:
        return OrderSide.BUY if data["m"] else OrderSide.SELL

    async def _route_user_data(self, data: Dict[str, Any]) -> None:
        if data["e"] == "outboundAccountPosition":
            if self.is_account_stream_subscribed:
                await self.user_data_queue["account"].put(data)
        elif data["e"] == "executionReport":
            if self.is_order_stream_subscribed:
                await self.user_data_queue["order"].put(data)
            if self.is_trade_stream_subscribed and data["x"] == "TRADE":
                await self.user_data_queue["trade"].put(data)
        else:
            self.logger.warning(f"Unknown user data event: {data}")

    @cached(_exchange_info_cache, key=lambda self, symbol: symbol)
    async def _to_symbol(self, symbol: str) -> Symbol:
        exchange_info = await self.websocket_client._rest_connector.get_exchange_info()
        for pair in exchange_info["symbols"]:
            if pair["symbol"] == symbol:
                return Symbol(
                    base_currency=pair["baseAsset"],
                    quote_currency=pair["quoteAsset"],
                    instrument_type=InstrumentType.SPOT,
                )
        raise ValueError(f"Symbol {symbol} not found in exchange info")

    async def order_updates_iterator(self) -> AsyncGenerator[Order, None]:
        if not self.is_user_data_stream_subscribed:
            await self.websocket_client.subscribe_user_data(self._route_user_data)
            self.is_user_data_stream_subscribed = True
        self.is_order_stream_subscribed = True
        try:
            while True:
                data = await self.user_data_queue["order"].get()
                symbol = await self._to_symbol(data["s"])
                yield Order(
                    symbol=symbol,
                    order_id=data["i"],
                    client_order_id=data["c"],
                    price=Decimal(data["p"]),
                    original_quantity=Decimal(data["q"]),
                    executed_quantity=Decimal(data["z"]),
                    side=OrderSide(data["S"]),
                    order_type=OrderType(data["o"]),
                    time_in_force=TimeInForce(data["f"]),
                    status=OrderStatus(data["X"]),
                    timestamp=data["W"],
                    update_time=data["T"],
                )
        except Exception as e:
            self.logger.error(f"Error in order_updates_iterator: {e}")
            raise e
        finally:
            self.is_order_stream_subscribed = False

    async def execution_updates_iterator(self) -> AsyncGenerator[MyTrade, None]:
        if not self.is_user_data_stream_subscribed:
            await self.websocket_client.subscribe_user_data(self._route_user_data)
            self.is_user_data_stream_subscribed = True
        self.is_trade_stream_subscribed = True
        try:
            while True:
                data = await self.user_data_queue["trade"].get()
                symbol = await self._to_symbol(data["s"])
                yield MyTrade(
                    id=data["t"],
                    symbol=symbol,
                    price=Decimal(data["p"]),
                    quantity=Decimal(data["q"]),
                    time=data["T"],
                    side=OrderSide(data["S"]),
                    is_maker=data["m"],
                    commission=Decimal(data["c"]),
                    commission_asset=data["n"],
                )
        except Exception as e:
            self.logger.error(f"Error in execution_updates_iterator: {e}")
            raise e
        finally:
            self.is_trade_stream_subscribed = False

    async def account_updates_iterator(self) -> AsyncGenerator[AccountBalance, None]:
        if not self.is_user_data_stream_subscribed:
            await self.websocket_client.subscribe_user_data(self._route_user_data)
            self.is_user_data_stream_subscribed = True
        self.is_account_stream_subscribed = True
        try:
            while True:
                data = await self.user_data_queue["account"].get()
                for balance in data["B"]:
                    yield AccountBalance(
                        asset=balance["a"],
                        free=Decimal(balance["f"]),
                        locked=Decimal(balance["l"]),
                    )

        except Exception as e:
            self.logger.error(f"Error in account_updates_iterator: {e}")
            raise e
        finally:
            self.is_account_stream_subscribed = False
