import asyncio
import logging
from typing import Callable, Dict
from solvexity.feed import Feed
from solvexity.connector.binance.websocket import BinanceWebSocketSubscriber
from solvexity.model.bar import Bar
from solvexity.eventbus.event import Event

logger = logging.getLogger(__name__)

class BinanceOHLCV(Feed):
    def __init__(self, symbol: str, interval: str):
        self.symbol = symbol
        self.interval = interval
        self.ws = BinanceWebSocketSubscriber(api_key="", api_secret="", use_testnet=False)

    async def subscribe(self, callback: Callable[[Event], None]) -> Callable[[], None]:
        async def event_handler(message: Dict):
            logger.info(f"Received message: {message}")
            bar = self.translate(message)
            if bar:
                await callback(Event(data=bar))
        return await self.ws.subscribe_kline(self.symbol, self.interval, event_handler)

    def translate(self, message: Dict) -> Bar | None:
        if message.get("e", None) != "kline":
            return None
        data = message["k"]
        return Bar(
            symbol=message["s"],
            interval=data["i"],
            open_time=int(data["t"]),
            close_time=int(data["T"]),
            open=float(data["o"]),
            high=float(data["h"]),
            low=float(data["l"]),
            close=float(data["c"]),
            volume=float(data["v"]),
            is_closed=data["x"],
        )