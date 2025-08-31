import asyncio
import json
import logging
import time
from typing import AsyncGenerator, Dict, Optional

import websockets

from solvexity.connector.binance.rest import BinanceRestClient

logger = logging.getLogger(__name__)

class BinanceUserDataStream:
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        use_testnet: bool = False,
        max_retries: int = 5,
    ):
        self.ws_url = "wss://stream.binance.com/ws/"
        if use_testnet:
            self.ws_url = "wss://testnet.binance.vision/ws/"
        self.max_retries = max_retries
        self._api_key = api_key
        self._api_secret = api_secret
        self._use_testnet = use_testnet
        self.rest_client: Optional[BinanceRestClient] = None
        self.listen_key: Optional[str] = None
        self.keep_alive_task: Optional[asyncio.Task] = None

    

    async def _initialize_rest_client(self):
        if self.rest_client:
            return
        self.rest_client = BinanceRestClient(self._api_key, self._api_secret, self._use_testnet)
        await self.rest_client.__aenter__()

    async def _cleanup_rest_client(self):
        if self.rest_client:
            await self.rest_client.__aexit__(None, None, None)
            self.rest_client = None
    
    async def _get_listen_key(self) -> str:
        """Get a new listen key from the REST API."""
        await self._initialize_rest_client()
        try:
            response = await self.rest_client.generate_listen_key()
            listen_key = response.get("listenKey")
            if not listen_key:
                raise ValueError("No listen key received from API")
            logger.info(f"Generated new listen key: {listen_key}")
            return listen_key
        except Exception as e:
            logger.error(f"Failed to generate listen key: {e}")
            raise

    async def _keep_alive_loop(self, listen_key: str):
        """Background task to keep the listen key alive every 30 minutes."""
        while True:
            try:
                await asyncio.sleep(30 * 60)  # 30 minutes
                await self.rest_client.keep_alive_listen_key(listen_key)
                logger.debug(f"Keep alive sent for listen key: {listen_key}")
            except asyncio.CancelledError:
                logger.info("Keep alive task cancelled")
                break
            except Exception as e:
                logger.error(f"Failed to keep alive listen key {listen_key}: {e}")
                break

    async def _cleanup_listen_key(self, listen_key: str):
        """Delete the listen key."""
        try:
            await self.rest_client.delete_listen_key(listen_key)
            logger.info(f"Deleted listen key: {listen_key}")
        except Exception as e:
            logger.error(f"Failed to delete listen key {listen_key}: {e}")

    async def _websocket_stream(self, ws_url: str) -> AsyncGenerator[Dict, None]:
        """Async generator that yields messages from a websocket connection with retry logic"""
        retry_count = 0
        base_delay = 1  # Start with 1 second delay
        max_connection_time = 23 * 3600 + 55 * 60  # 23 hours 55 minutes in seconds

        while retry_count <= self.max_retries:
            try:
                # Get a new listen key for each connection attempt
                if not self.listen_key:
                    self.listen_key = await self._get_listen_key()
                
                # Start keep alive task
                if self.keep_alive_task:
                    self.keep_alive_task.cancel()
                self.keep_alive_task = asyncio.create_task(self._keep_alive_loop(self.listen_key))

                logger.info(
                    f"Connecting to User Data WebSocket: {ws_url} (attempt {retry_count + 1}/{self.max_retries + 1})"
                )
                async with websockets.connect(ws_url) as ws:
                    logger.info(f"Successfully connected to User Data WebSocket: {ws_url}")
                    retry_count = 0  # Reset retry count on successful connection

                    # Record connection start time
                    connection_start = time.time()
                    logger.info(
                        f"Connection started at {connection_start} for {ws_url}"
                    )

                    # Start connection timeout task
                    async def connection_timeout():
                        await asyncio.sleep(max_connection_time)
                        logger.info(
                            f"Connection timeout reached for {ws_url} (23h 55m), closing connection for reconnection"
                        )
                        await ws.close()

                    timeout_task = asyncio.create_task(connection_timeout())

                    try:
                        async for message in ws:
                            # Check if we need to reconnect due to time limit
                            current_time = time.time()
                            connection_duration = current_time - connection_start

                            if connection_duration >= max_connection_time:
                                logger.info(
                                    f"Connection duration ({connection_duration:.0f}s) exceeded limit for {ws_url}, reconnecting..."
                                )
                                break

                            # Handle regular messages
                            logger.debug(f"Received message from {ws_url}: {message}")

                            # Parse string message to dict
                            try:
                                if isinstance(message, str):
                                    message_dict = json.loads(message)
                                else:
                                    message_dict = message

                                yield message_dict
                            except json.JSONDecodeError as e:
                                logger.error(
                                    f"Failed to parse JSON message from {ws_url}: {e}"
                                )
                                logger.error(f"Raw message: {message}")
                            except Exception as e:
                                logger.error(
                                    f"Error processing message from {ws_url}: {e}"
                                )
                                logger.error(f"Message: {message}")
                    finally:
                        # Cancel timeout task
                        timeout_task.cancel()
                        try:
                            await timeout_task
                        except asyncio.CancelledError:
                            pass

            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"User Data WebSocket connection closed for {ws_url}: {e}")
                
                # Clean up current listen key and get a new one
                if self.listen_key:
                    await self._cleanup_listen_key(self.listen_key)
                    self.listen_key = None
                
                if retry_count < self.max_retries:
                    retry_count += 1
                    delay = base_delay * (2 ** (retry_count - 1))  # Exponential backoff
                    logger.info(f"Retrying connection in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Max retries ({self.max_retries}) reached for {ws_url}. Stopping reconnection attempts.",
                        exc_info=True,
                    )
                    break

            except websockets.exceptions.InvalidURI as e:
                logger.error(f"Invalid WebSocket URI {ws_url}: {e}", exc_info=True)
                break

            except Exception as e:
                logger.error(
                    f"Unexpected WebSocket error for {ws_url}: {e}", exc_info=True
                )
                
                # Clean up current listen key and get a new one
                if self.listen_key:
                    await self._cleanup_listen_key(self.listen_key)
                    self.listen_key = None
                
                if retry_count < self.max_retries:
                    retry_count += 1
                    delay = base_delay * (2 ** (retry_count - 1))
                    logger.info(f"Retrying connection in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Max retries ({self.max_retries}) reached for {ws_url}. Stopping reconnection attempts.",
                        exc_info=True,
                    )
                    break

        if retry_count > self.max_retries:
            logger.error(
                f"Failed to establish User Data WebSocket connection after {self.max_retries} retries for {ws_url}",
                exc_info=True,
            )

    async def recv_user_data(self) -> AsyncGenerator[Dict, None]:
        """Async generator that yields user data messages from the websocket stream.
        
        This includes:
        - Order updates
        - Account updates
        - Balance updates
        - Other user-specific events
        """
        if not self.listen_key:
            self.listen_key = await self._get_listen_key()
        
        ws_url = f"{self.ws_url}{self.listen_key}"
        
        async for message in self._websocket_stream(ws_url):
            yield message

    async def close(self):
        """Clean up resources and close the connection."""
        if self.keep_alive_task:
            self.keep_alive_task.cancel()
            try:
                await self.keep_alive_task
            except asyncio.CancelledError:
                pass
        
        if self.listen_key:
            await self._cleanup_listen_key(self.listen_key)
            self.listen_key = None
        
        if self.rest_client:
            await self._cleanup_rest_client()
            self.rest_client = None




class BinanceMarketDataStream:
    def __init__(
        self,
        use_testnet: bool = False,
        max_retries: int = 5,
    ):
        self.ws_url = "wss://stream.binance.com/ws/"
        if use_testnet:
            self.ws_url = "wss://testnet.binance.vision/ws/"
        self.max_retries = max_retries

    async def _websocket_stream(self, ws_url: str) -> AsyncGenerator[Dict, None]:
        """Async generator that yields messages from a websocket connection with retry logic"""
        retry_count = 0
        base_delay = 1  # Start with 1 second delay
        max_connection_time = 23 * 3600 + 55 * 60  # 23 hours 55 minutes in seconds

        while retry_count <= self.max_retries:
            try:
                logger.info(
                    f"Connecting to WebSocket: {ws_url} (attempt {retry_count + 1}/{self.max_retries + 1})"
                )
                async with websockets.connect(ws_url) as ws:
                    logger.info(f"Successfully connected to WebSocket: {ws_url}")
                    retry_count = 0  # Reset retry count on successful connection

                    # Record connection start time
                    connection_start = time.time()
                    logger.info(
                        f"Connection started at {connection_start} for {ws_url}"
                    )



                    # Start connection timeout task
                    async def connection_timeout():
                        await asyncio.sleep(max_connection_time)
                        logger.info(
                            f"Connection timeout reached for {ws_url} (23h 55m), closing connection for reconnection"
                        )
                        await ws.close()

                    timeout_task = asyncio.create_task(connection_timeout())

                    try:
                        async for message in ws:
                            # Check if we need to reconnect due to time limit
                            current_time = time.time()
                            connection_duration = current_time - connection_start

                            if connection_duration >= max_connection_time:
                                logger.info(
                                    f"Connection duration ({connection_duration:.0f}s) exceeded limit for {ws_url}, reconnecting..."
                                )
                                break

                            # Handle regular messages
                            logger.debug(f"Received message from {ws_url}: {message}")

                            # Parse string message to dict
                            try:
                                if isinstance(message, str):
                                    message_dict = json.loads(message)
                                else:
                                    message_dict = message

                                yield message_dict
                            except json.JSONDecodeError as e:
                                logger.error(
                                    f"Failed to parse JSON message from {ws_url}: {e}"
                                )
                                logger.error(f"Raw message: {message}")
                            except Exception as e:
                                logger.error(
                                    f"Error processing message from {ws_url}: {e}"
                                )
                                logger.error(f"Message: {message}")
                    finally:
                        # Cancel timeout task
                        timeout_task.cancel()
                        try:
                            await timeout_task
                        except asyncio.CancelledError:
                            pass

            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"WebSocket connection closed for {ws_url}: {e}")
                if retry_count < self.max_retries:
                    retry_count += 1
                    delay = base_delay * (2 ** (retry_count - 1))  # Exponential backoff
                    logger.info(f"Retrying connection in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Max retries ({self.max_retries}) reached for {ws_url}. Stopping reconnection attempts.",
                        exc_info=True,
                    )
                    break

            except websockets.exceptions.InvalidURI as e:
                logger.error(f"Invalid WebSocket URI {ws_url}: {e}", exc_info=True)
                break

            except Exception as e:
                logger.error(
                    f"Unexpected WebSocket error for {ws_url}: {e}", exc_info=True
                )
                if retry_count < self.max_retries:
                    retry_count += 1
                    delay = base_delay * (2 ** (retry_count - 1))
                    logger.info(f"Retrying connection in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Max retries ({self.max_retries}) reached for {ws_url}. Stopping reconnection attempts.",
                        exc_info=True,
                    )
                    break

        if retry_count > self.max_retries:
            logger.error(
                f"Failed to establish WebSocket connection after {self.max_retries} retries for {ws_url}",
                exc_info=True,
            )

    async def recv_kline(
        self, symbol: str, interval: str
    ) -> AsyncGenerator[Dict, None]:
        """Async generator that yields kline messages from a websocket stream"""
        channel = f"{symbol.lower()}@kline_{interval}"
        ws_url = f"{self.ws_url}{channel}"
        
        async for message in self._websocket_stream(ws_url):
            yield message

    async def recv_trade(
        self, symbol: str
    ) -> AsyncGenerator[Dict, None]:
        """Async generator that yields trade messages from a websocket stream
        {'e': 'trade', 'E': 1756472631251, 's': 'BTCUSDT', 't': 5200588973, 'p': '110653.47000000', 'q': '0.00005000', 'T': 1756472631251, 'm': True, 'M': True}
        """
        channel = f"{symbol.lower()}@trade"
        ws_url = f"{self.ws_url}{channel}"
        
        async for message in self._websocket_stream(ws_url):
            yield message

    async def recv_stream(
        self, channel: str
    ) -> AsyncGenerator[Dict, None]:
        """Async generator that yields messages from a custom websocket stream"""
        ws_url = f"{self.ws_url}{channel}"
        
        async for message in self._websocket_stream(ws_url):
            yield message
