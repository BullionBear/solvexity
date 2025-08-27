import logging
from typing import Callable, Dict
import asyncio
from solvexity.connector.binance.rest import BinanceRestClient
import websockets

logger = logging.getLogger(__name__)

class BinanceWebSocketSubscriber:
    def __init__(self, api_key: str, api_secret: str, use_testnet: bool = False, max_retries: int = 5):
        self.rest_client = BinanceRestClient(api_key, api_secret, use_testnet)
        self.ws_url = "wss://fstream.binance.com/ws/"
        if use_testnet:
            self.ws_url = "wss://testnet.binance.vision/ws/"
        self.callbacks: Dict[str, Callable[[Dict], None]] = {} # url -> callback
        self.tasks: Dict[str, asyncio.Task] = {} # url -> task
        self.max_retries = max_retries

    async def _handle_websocket(self, channel: str, callback: Callable[[Dict], None]):
        """Background task to handle websocket connection and messages with retry logic"""
        retry_count = 0
        base_delay = 1  # Start with 1 second delay
        ws_raw_url = self.ws_url + channel
        while retry_count <= self.max_retries:
            try:
                logger.info(f"Connecting to WebSocket: {channel} (attempt {retry_count + 1}/{self.max_retries + 1})")
                async with websockets.connect(ws_raw_url) as ws:
                    logger.info(f"Successfully connected to WebSocket: {ws_raw_url}")
                    retry_count = 0  # Reset retry count on successful connection
                    
                    async for message in ws:
                        if asyncio.iscoroutinefunction(callback):
                            asyncio.create_task(callback(message))
                        else:
                            callback(message)
                            
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"WebSocket connection closed for {ws_raw_url}: {e}")
                if retry_count < self.max_retries:
                    retry_count += 1
                    delay = base_delay * (2 ** (retry_count - 1))  # Exponential backoff
                    logger.info(f"Retrying connection in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Max retries ({self.max_retries}) reached for {ws_raw_url}. Stopping reconnection attempts.")
                    break
                    
            except websockets.exceptions.InvalidURI as e:
                logger.error(f"Invalid WebSocket URI {ws_raw_url}: {e}")
                break
                
            except Exception as e:
                logger.error(f"Unexpected WebSocket error for {ws_raw_url}: {e}")
                if retry_count < self.max_retries:
                    retry_count += 1
                    delay = base_delay * (2 ** (retry_count - 1))
                    logger.info(f"Retrying connection in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Max retries ({self.max_retries}) reached for {ws_raw_url}. Stopping reconnection attempts.")
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
        return await self.subscribe(channel, callback)

   