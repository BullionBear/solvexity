import asyncio
import json
import logging
import time
from typing import AsyncGenerator, Dict

import websockets

from solvexity.connector.binance.rest import BinanceRestClient

logger = logging.getLogger(__name__)


class BinanceWebSocketSubscriber:
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        use_testnet: bool = False,
        max_retries: int = 5,
    ):
        self.rest_client = BinanceRestClient(api_key, api_secret, use_testnet)
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

                    # Start periodic pong task (every 30 seconds as safety measure)
                    async def send_periodic_pong():
                        while True:
                            try:
                                await asyncio.sleep(30)
                                await ws.pong(b"")  # Empty payload as recommended
                                logger.debug(f"Sent periodic pong to {ws_url}")
                            except Exception as e:
                                logger.debug(f"Failed to send periodic pong: {e}")
                                break

                    pong_task = asyncio.create_task(send_periodic_pong())

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
                        # Cancel periodic pong task
                        pong_task.cancel()
                        timeout_task.cancel()
                        try:
                            await pong_task
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
        """Async generator that yields trade messages from a websocket stream"""
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
