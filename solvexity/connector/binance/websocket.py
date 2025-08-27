import logging
from typing import Callable, Dict
import asyncio
import time
from solvexity.connector.binance.rest import BinanceRestClient
import websockets

logger = logging.getLogger(__name__)

class BinanceWebSocketSubscriber:
    def __init__(self, api_key: str, api_secret: str, use_testnet: bool = False, max_retries: int = 5):
        self.rest_client = BinanceRestClient(api_key, api_secret, use_testnet)
        self.ws_url = "wss://stream.binance.com/ws/"
        if use_testnet:
            self.ws_url = "wss://testnet.binance.vision/ws/"
        self.callbacks: Dict[str, Callable[[Dict], None]] = {} # url -> callback
        self.tasks: Dict[str, asyncio.Task] = {} # url -> task
        self.max_retries = max_retries
        self.connection_start_times: Dict[str, float] = {}  # channel -> start_time

    async def _handle_websocket(self, ws_url: str, callback: Callable[[Dict], None]):
        """Background task to handle websocket connection and messages with retry logic"""
        retry_count = 0
        base_delay = 1  # Start with 1 second delay
        max_connection_time = 23 * 3600 + 55 * 60  # 23 hours 55 minutes in seconds
        
        while retry_count <= self.max_retries:
            try:
                logger.info(f"Connecting to WebSocket: {ws_url} (attempt {retry_count + 1}/{self.max_retries + 1})")
                async with websockets.connect(ws_url) as ws:
                    logger.info(f"Successfully connected to WebSocket: {ws_url}")
                    retry_count = 0  # Reset retry count on successful connection
                    
                    # Record connection start time
                    connection_start = time.time()
                    self.connection_start_times[ws_url] = connection_start
                    logger.info(f"Connection started at {connection_start} for {ws_url}")
                    
                    # Start periodic pong task (every 30 seconds as safety measure)
                    async def send_periodic_pong():
                        while True:
                            try:
                                await asyncio.sleep(30)
                                await ws.pong(b'')  # Empty payload as recommended
                                logger.debug(f"Sent periodic pong to {ws_url}")
                            except Exception as e:
                                logger.debug(f"Failed to send periodic pong: {e}")
                                break
                    
                    pong_task = asyncio.create_task(send_periodic_pong())
                    
                    # Start connection timeout task
                    async def connection_timeout():
                        await asyncio.sleep(max_connection_time)
                        logger.info(f"Connection timeout reached for {ws_url} (23h 55m), closing connection for reconnection")
                        await ws.close()
                    
                    timeout_task = asyncio.create_task(connection_timeout())
                    
                    try:
                        async for message in ws:
                            # Check if we need to reconnect due to time limit
                            current_time = time.time()
                            connection_duration = current_time - connection_start
                            
                            if connection_duration >= max_connection_time:
                                logger.info(f"Connection duration ({connection_duration:.0f}s) exceeded limit for {ws_url}, reconnecting...")
                                break
                            
                            # Handle ping frames (websockets library handles ping/pong automatically)
                            # We don't need to manually handle ping frames
                            
                            # Handle regular messages
                            logger.debug(f"Received message from {ws_url}: {message}")
                            if asyncio.iscoroutinefunction(callback):
                                asyncio.create_task(callback(message))
                            else:
                                callback(message)
                    finally:
                        # Cancel periodic pong task
                        pong_task.cancel()
                        timeout_task.cancel()
                        try:
                            await pong_task
                            await timeout_task
                        except asyncio.CancelledError:
                            pass
                        
                        # Clean up connection start time
                        if ws_url in self.connection_start_times:
                            del self.connection_start_times[ws_url]
                            
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"WebSocket connection closed for {ws_url}: {e}")
                if retry_count < self.max_retries:
                    retry_count += 1
                    delay = base_delay * (2 ** (retry_count - 1))  # Exponential backoff
                    logger.info(f"Retrying connection in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Max retries ({self.max_retries}) reached for {ws_url}. Stopping reconnection attempts.")
                    break
                    
            except websockets.exceptions.InvalidURI as e:
                logger.error(f"Invalid WebSocket URI {ws_url}: {e}")
                break
                
            except Exception as e:
                logger.error(f"Unexpected WebSocket error for {ws_url}: {e}")
                if retry_count < self.max_retries:
                    retry_count += 1
                    delay = base_delay * (2 ** (retry_count - 1))
                    logger.info(f"Retrying connection in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Max retries ({self.max_retries}) reached for {ws_url}. Stopping reconnection attempts.")
                    break
        
        if retry_count > self.max_retries:
            logger.error(f"Failed to establish WebSocket connection after {self.max_retries} retries for {ws_url}")


    async def subscribe(self, ws_url: str, callback: Callable[[Dict], None]) -> Callable[[], None]:
        """Subscribe to a websocket stream non-blocking"""
        self.callbacks[ws_url] = callback
        
        task = asyncio.create_task(self._handle_websocket(ws_url, callback))
        self.tasks[ws_url] = task
        
        # Return unsubscribe function
        def unsubscribe():
            if ws_url in self.tasks:
                self.tasks[ws_url].cancel()
                del self.tasks[ws_url]
            if ws_url in self.callbacks:
                del self.callbacks[ws_url]
        
        return unsubscribe

    async def subscribe_kline(self, symbol: str, interval: str, callback: Callable[[Dict], None]) -> Callable[[], None]:
        """Subscribe to a kline stream non-blocking"""
        channel = f"{symbol.lower()}@kline_{interval}"
        return await self.subscribe(f"{self.ws_url}{channel}", callback)

   