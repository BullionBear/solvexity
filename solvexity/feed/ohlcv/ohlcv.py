import asyncio
import logging
from typing import AsyncGenerator, Callable, Dict

from solvexity.connector.binance import BinanceMarketDataStream
from solvexity.eventbus.event import Event
from solvexity.feed import Feed
from solvexity.model.bar import Bar
from solvexity.model.enum import Symbol, Exchange

logger = logging.getLogger(__name__)


class OHLCV(Feed):
    def __init__(self, symbol: Symbol, exchange: Exchange, interval: str):
        self.symbol = symbol
        self.exchange = exchange
        self.interval = interval
        self.ws = BinanceMarketDataStream(
            use_testnet=False
        )

    async def recv(self) -> AsyncGenerator[Bar, None]:
        if self.exchange == Exchange.BINANCE:
            symbol = self.symbol.base + self.symbol.quote
        async for message in self.ws.recv_kline(symbol, self.interval):
            yield self.translate(message)

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
