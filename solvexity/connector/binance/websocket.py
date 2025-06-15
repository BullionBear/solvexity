import asyncio
import json
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional

import websockets

from solvexity.logger import SolvexityLogger

from .rest import BinanceRestClient

class BinanceWebSocketClient:
    """Binance WebSocket API client for real-time data streaming."""

    BASE_URL = "wss://stream.binance.com/ws"
    TESTNET_URL = "wss://stream.testnet.binance.vision/ws"

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        use_testnet: bool = False,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.use_testnet = use_testnet
        self.ws_url = self.TESTNET_URL if use_testnet else self.BASE_URL
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self._subscriptions: Dict[
            str, List[Callable[[Dict[str, Any]], Awaitable[None]]]
        ] = {}
        self._running = False
        self._listen_task: Optional[asyncio.Task] = None
        self._rest_connector: Optional[BinanceRestClient] = None  # Will be initialized in connect()
        self._listen_key: Optional[str] = None
        self._keep_alive_task: Optional[asyncio.Task] = None
        self.logger = SolvexityLogger().get_logger(__name__)

    async def connect(self) -> None:
        """Establish WebSocket connection."""
        if self.ws:
            return

        # Initialize REST connector with async context manager

        self._rest_connector = BinanceRestClient(
            self.api_key, self.api_secret, self.use_testnet
        )

        await self._rest_connector.__aenter__()

        self.ws = await websockets.connect(self.ws_url)
        self._running = True
        self._listen_task = asyncio.create_task(self._listen())

    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        self._running = False
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        if self._keep_alive_task:
            self._keep_alive_task.cancel()
            try:
                await self._keep_alive_task
            except asyncio.CancelledError:
                pass
        if self._listen_key and self._rest_connector:
            await self._rest_connector.delete_listen_key(self._listen_key)
        if self.ws:
            await self.ws.close()
            self.ws = None
        if self._rest_connector:
            await self._rest_connector.__aexit__(None, None, None)
            self._rest_connector = None

    async def _keep_alive_listen_key(self) -> None:
        """Keep the listen key alive by sending periodic requests."""
        while self._running and self._listen_key:
            try:
                await self._rest_connector.keep_alive_listen_key(self._listen_key)
                await asyncio.sleep(30 * 60)  # Keep alive every 30 minutes
            except Exception as e:
                self.logger.error(f"Error keeping listen key alive: {e}")
                await asyncio.sleep(5)

    async def _get_listen_key(self) -> str:
        """Get a listen key for user data stream."""
        if not self._listen_key:
            response = await self._rest_connector.generate_listen_key()
            self._listen_key = response["listenKey"]
            # Start keep-alive task
            self._keep_alive_task = asyncio.create_task(self._keep_alive_listen_key())
        return self._listen_key

    async def _resubscribe_all(self) -> None:
        """Resubscribe to all previously subscribed streams."""
        if not self.ws:
            return

        for stream in self._subscriptions.keys():
            await self.ws.send(
                json.dumps(
                    {
                        "method": "SUBSCRIBE",
                        "params": [stream],
                        "id": int(time.time() * 1000),
                    }
                )
            )

    async def _listen(self) -> None:
        """Listen for incoming WebSocket messages."""
        while self._running:
            try:
                message = await self.ws.recv()
                await self._handle_message(json.loads(message))
            except websockets.exceptions.ConnectionClosed:
                self.logger.warning(
                    "WebSocket connection closed. Attempting to reconnect..."
                )
                await asyncio.sleep(5)
                await self.connect()
                # Resubscribe to all streams after reconnection
                await self._resubscribe_all()
            except Exception as e:
                self.logger.error(f"Error in WebSocket listener: {e}")
                await asyncio.sleep(5)

    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle incoming WebSocket messages."""
        self.logger.debug(f"Received message: {message}")  # Debug log

        if "stream" in message:
            # Handle combined stream messages
            stream = message["stream"]
            data = message["data"]
            if stream in self._subscriptions:
                for callback in self._subscriptions[stream]:
                    await callback(data)
        else:
            # Handle single stream messages
            # For ticker updates
            if "e" in message and message["e"] == "24hrTicker":
                stream = f"{message['s'].lower()}@ticker"
                if stream in self._subscriptions:
                    for callback in self._subscriptions[stream]:
                        await callback(message)

            # For orderbook updates
            elif "e" in message and message["e"] == "depthUpdate":
                stream = f"{message['s'].lower()}@depth"
                if stream in self._subscriptions:
                    for callback in self._subscriptions[stream]:
                        await callback(message)

            # For trade updates
            elif "e" in message and message["e"] == "trade":
                stream = f"{message['s'].lower()}@trade"
                if stream in self._subscriptions:
                    for callback in self._subscriptions[stream]:
                        await callback(message)

            # For user data updates
            elif "e" in message and message["e"] in [
                "outboundAccountPosition",
                "balanceUpdate",
                "executionReport",
            ]:
                if self._listen_key in self._subscriptions:
                    for callback in self._subscriptions[self._listen_key]:
                        await callback(message)

    async def subscribe_ticker(
        self, symbol: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Subscribe to ticker updates for a symbol."""
        stream = f"{symbol.lower()}@ticker"
        await self._subscribe_stream(stream, callback)

    async def subscribe_orderbook(
        self, symbol: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Subscribe to orderbook updates for a symbol."""
        stream = f"{symbol.lower()}@depth"
        await self._subscribe_stream(stream, callback)

    async def unsubscribe_orderbook(self, symbol: str) -> None:
        """Unsubscribe from orderbook updates for a symbol."""
        stream = f"{symbol.lower()}@depth"
        if stream in self._subscriptions:
            del self._subscriptions[stream]
            if self.ws:
                await self.ws.send(
                    json.dumps(
                        {
                            "method": "UNSUBSCRIBE",
                            "params": [stream],
                            "id": int(time.time() * 1000),
                        }
                    )
                )

    async def subscribe_orderbook_100ms(
        self, symbol: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Subscribe to orderbook updates for a symbol at 100ms intervals."""
        stream = f"{symbol.lower()}@depth@100ms"
        await self._subscribe_stream(stream, callback)

    async def unsubscribe_orderbook_100ms(self, symbol: str) -> None:
        """Unsubscribe from orderbook updates for a symbol at 100ms intervals."""
        stream = f"{symbol.lower()}@depth@100ms"
        if stream in self._subscriptions:
            del self._subscriptions[stream]
            if self.ws:
                await self.ws.send(
                    json.dumps(
                        {
                            "method": "UNSUBSCRIBE",
                            "params": [stream],
                            "id": int(time.time() * 1000),
                        }
                    )
                )

    async def subscribe_trades(
        self, symbol: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Subscribe to trade updates for a symbol."""
        stream = f"{symbol.lower()}@trade"
        await self._subscribe_stream(stream, callback)

    async def unsubscribe_trades(self, symbol: str) -> None:
        """Unsubscribe from trade updates for a symbol."""
        stream = f"{symbol.lower()}@trade"
        if stream in self._subscriptions:
            del self._subscriptions[stream]
            if self.ws:
                await self.ws.send(
                    json.dumps(
                        {
                            "method": "UNSUBSCRIBE",
                            "params": [stream],
                            "id": int(time.time() * 1000),
                        }
                    )
                )

    async def subscribe_kline(
        self,
        symbol: str,
        interval: str,
        callback: Callable[[Dict[str, Any]], Awaitable[None]],
    ) -> None:
        """Subscribe to kline/candlestick updates for a symbol."""
        stream = f"{symbol.lower()}@kline_{interval}"
        await self._subscribe_stream(stream, callback)

    async def unsubscribe_kline(self, symbol: str, interval: str) -> None:
        """Unsubscribe from kline/candlestick updates for a symbol."""
        stream = f"{symbol.lower()}@kline_{interval}"
        if stream in self._subscriptions:
            del self._subscriptions[stream]
            if self.ws:
                await self.ws.send(
                    json.dumps(
                        {
                            "method": "UNSUBSCRIBE",
                            "params": [stream],
                            "id": int(time.time() * 1000),
                        }
                    )
                )

    async def subscribe_user_data(
        self, callback: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Subscribe to user data updates (orders, balance, etc.)."""
        if not self.api_key or not self.api_secret:
            raise ValueError("API key and secret are required for user data stream")

        # Generate listen key
        listen_key = await self._get_listen_key()

        # Subscribe to user data stream
        stream = f"{listen_key}"
        await self._subscribe_stream(stream, callback)

    async def unsubscribe_user_data(self) -> None:
        """Unsubscribe from user data updates."""
        if self._listen_key in self._subscriptions:
            del self._subscriptions[self._listen_key]
            if self.ws:
                await self.ws.send(
                    json.dumps(
                        {
                            "method": "UNSUBSCRIBE",
                            "params": [self._listen_key],
                            "id": int(time.time() * 1000),
                        }
                    )
                )
            self._listen_key = None
            if self._keep_alive_task:
                self._keep_alive_task.cancel()
                self._keep_alive_task = None

    async def _subscribe_stream(
        self, stream: str, callback: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Subscribe to a WebSocket stream."""
        if not self.ws:
            await self.connect()

        if stream not in self._subscriptions:
            self._subscriptions[stream] = []
            # Send subscription message
            await self.ws.send(
                json.dumps(
                    {
                        "method": "SUBSCRIBE",
                        "params": [stream],
                        "id": int(time.time() * 1000),
                    }
                )
            )

        self._subscriptions[stream].append(callback)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
