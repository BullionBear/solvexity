from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union, AsyncGenerator
import websockets
import asyncio
from solvexity.connector.types import OHLCV, OrderBook, Symbol, Trade, Order, AccountBalance
from solvexity.connector.types import OrderSide, OrderType

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
    async def create_order(self, symbol: Symbol, side: OrderSide, order_type: OrderType, 
                         quantity: Decimal, price: Optional[Decimal] = None) -> Dict[str, Any]:
        """Create a new order."""
        pass
        
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: Symbol) -> Dict[str, Any]:
        """Cancel an existing order."""
        pass

    @abstractmethod
    async def get_open_orders(self, symbol: Symbol) -> List[Order]:
        """Get open orders for a symbol."""
        pass
        
    @abstractmethod
    async def get_order_status(self, order_id: str|int, symbol: Symbol) -> Order:
        """Get status of an order."""
        pass
        
    @abstractmethod
    async def get_account_balance(self) -> List[AccountBalance]:
        """Get account balance information."""
        pass

    @abstractmethod
    async def get_my_trades(self, symbol: Symbol, limit: int = 100) -> List[Trade]:
        """Get my trades for a symbol."""
        pass


class ExchangeWebSocketConnector(ABC):

    @abstractmethod
    async def __aenter__(self):
        """Async context manager enter."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass

    @abstractmethod
    async def depth_diff_iterator(self, symbol: Symbol) -> AsyncGenerator[OrderBook, None]:
        """Return an async generator that yields the latest order book updates for a symbol.
        
        Usage:
            async for update in connector.depth_diff_iterator(symbol):
                # Process order book update
        """
        pass

    @abstractmethod
    async def public_trades_iterator(self, symbol: Symbol) -> AsyncGenerator[Trade, None]:
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
