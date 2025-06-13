from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import aiohttp
import websockets
import json
import asyncio
from datetime import datetime
import hmac
import hashlib
import time


class ExchangeConnector(ABC):
    """Abstract base class for exchange connectors implementing REST and WebSocket functionality."""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, passphrase: Optional[str] = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
        if self.ws:
            await self.ws.close()
            
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current ticker information for a symbol."""
        pass
        
    @abstractmethod
    async def get_orderbook(self, symbol: str, depth: int = 20) -> Dict[str, Any]:
        """Get order book for a symbol."""
        pass
        
    @abstractmethod
    async def get_recent_trades(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent trades for a symbol."""
        pass
        
    @abstractmethod
    async def create_order(self, symbol: str, side: str, order_type: str, 
                         quantity: float, price: Optional[float] = None) -> Dict[str, Any]:
        """Create a new order."""
        pass
        
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel an existing order."""
        pass
        
    @abstractmethod
    async def get_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Get status of an order."""
        pass
        
    @abstractmethod
    async def get_account_balance(self) -> Dict[str, float]:
        """Get account balance information."""
        pass
        
    # WebSocket methods
    @abstractmethod
    async def connect_websocket(self) -> None:
        """Establish WebSocket connection."""
        pass
        
    @abstractmethod
    async def subscribe_ticker(self, symbol: str) -> None:
        """Subscribe to ticker updates for a symbol."""
        pass
        
    @abstractmethod
    async def subscribe_orderbook(self, symbol: str) -> None:
        """Subscribe to orderbook updates for a symbol."""
        pass
        
    @abstractmethod
    async def subscribe_trades(self, symbol: str) -> None:
        """Subscribe to trade updates for a symbol."""
        pass
        
    @abstractmethod
    async def subscribe_user_data(self) -> None:
        """Subscribe to user data updates (orders, balance, etc.)."""
        pass
        
    @abstractmethod
    async def handle_websocket_message(self, message: str) -> None:
        """
        Handle incoming WebSocket messages.
        
        Example implementation for a specific exchange:
        ```python
        async def handle_websocket_message(self, message: str) -> None:
            data = json.loads(message)
            
            # Handle different message types
            if 'type' in data:
                if data['type'] == 'ticker':
                    # Process ticker update
                    symbol = data['symbol']
                    price = data['price']
                    # Update your local state or notify subscribers
                    
                elif data['type'] == 'orderbook':
                    # Process orderbook update
                    symbol = data['symbol']
                    bids = data['bids']
                    asks = data['asks']
                    # Update your local orderbook
                    
                elif data['type'] == 'trade':
                    # Process trade update
                    symbol = data['symbol']
                    price = data['price']
                    quantity = data['quantity']
                    # Update your local trade history
                    
                elif data['type'] == 'order':
                    # Process order update
                    order_id = data['orderId']
                    status = data['status']
                    # Update your local order state
        ```
        """
        pass
        
    async def start_websocket_listener(self) -> None:
        """
        Start listening to WebSocket messages.
        
        Example usage:
        ```python
        # Create and start the WebSocket listener
        connector = YourExchangeConnector(api_key, api_secret)
        async with connector:
            # Start the WebSocket listener in the background
            listener_task = asyncio.create_task(connector.start_websocket_listener())
            
            # Subscribe to different channels
            await connector.subscribe_ticker('BTC/USDT')
            await connector.subscribe_orderbook('BTC/USDT')
            
            # Keep the program running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                # Clean up
                listener_task.cancel()
        ```
        """
        if not self.ws:
            await self.connect_websocket()
            
        while True:
            try:
                message = await self.ws.recv()
                await self.handle_websocket_message(message)
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket connection closed. Attempting to reconnect...")
                await asyncio.sleep(5)
                await self.connect_websocket()
            except Exception as e:
                print(f"Error in WebSocket listener: {e}")
                await asyncio.sleep(5)
