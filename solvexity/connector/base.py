import asyncio
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, AsyncGenerator, Dict, List, Optional

import websockets

from solvexity.connector.types import (AccountBalance, MyTrade, Order,
                                       OrderBook, OrderBookUpdate, OrderSide,
                                       OrderType, Symbol, Trade)


class ExchangeConnector(ABC):
    """Abstract base class for exchange connectors implementing REST and WebSocket functionality."""

    @abstractmethod
    async def __aenter__(self):
        """Async context manager enter."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass

    @abstractmethod
    async def get_orderbook(self, symbol: Symbol, depth: int = 20) -> OrderBook:
        """Get order book for a symbol."""
        pass

    @abstractmethod
    async def get_recent_trades(self, symbol: Symbol, limit: int = 100) -> List[Trade]:
        """Get aggregate trades for a symbol."""
        pass

    @abstractmethod
    async def create_order(
        self,
        symbol: Symbol,
        side: OrderSide,
        order_type: OrderType,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new order."""
        pass

    @abstractmethod
    async def cancel_order(
        self,
        symbol: Symbol,
        order_id: Optional[str] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Cancel an existing order."""
        pass

    @abstractmethod
    async def get_open_orders(self, symbol: Symbol) -> List[Order]:
        """Get open orders for a symbol."""
        pass

    @abstractmethod
    async def get_order_status(
        self,
        symbol: Symbol,
        order_id: Optional[str] = None,
        client_order_id: Optional[str] = None,
    ) -> Order:
        """Get status of an order."""
        pass

    @abstractmethod
    async def get_account_balance(self) -> List[AccountBalance]:
        """Get account balance information."""
        pass

    @abstractmethod
    async def get_my_trades(self, symbol: Symbol, limit: int = 100) -> List[MyTrade]:
        """Get my trades for a symbol."""
        pass


class ExchangeStreamConnector(ABC):

    @abstractmethod
    async def __aenter__(self):
        """Async context manager enter."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass

    @abstractmethod
    async def depth_diff_iterator(
        self, symbol: Symbol
    ) -> AsyncGenerator[OrderBookUpdate, None]:
        """Return an async generator that yields the latest order book updates for a symbol.

        Usage:
            async for update in connector.depth_diff_iterator(symbol):
                # Process order book update
        """
        pass

    @abstractmethod
    async def public_trades_iterator(
        self, symbol: Symbol
    ) -> AsyncGenerator[Trade, None]:
        """Return an async generator that yields the latest trades for a symbol.

        Usage:
            async for trade in connector.public_trades_iterator(symbol):
                # Process trade update
        """
        pass

    @abstractmethod
    async def order_updates_iterator(self) -> AsyncGenerator[Order, None]:
        """Return an async generator that yields the latest order updates.

        Usage:
            async for order in connector.order_updates_iterator():
                # Process order update
        """
        pass

    @abstractmethod
    async def execution_updates_iterator(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Return an async generator that yields the latest execution updates.

        Usage:
            async for execution in connector.execution_updates_iterator():
                # Process execution update
        """
        pass

    @abstractmethod
    async def account_updates_iterator(self) -> AsyncGenerator[AccountBalance, None]:
        """Return an async generator that yields the latest account balance updates.

        Usage:
            async for balance in connector.account_updates_iterator():
                # Process balance update
        """
        pass
