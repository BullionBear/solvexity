import logging
from typing import Any
import bisect
from solvexity.alert import DiscordWebhook
from hooklet.base import BasePilot
from hooklet.eventrix.handler import Handler
from hooklet.types import MessageHandlerCallback

logger = logging.getLogger(__name__)


class OCHLVPriceAlert(Handler):
    def __init__(self, pilot: BasePilot, price_thresholds: list[float], webhook_url: str, subject: str, executor_id: str|None = None):
        super().__init__(pilot, executor_id)
        self._price_threshold: list[float] = price_thresholds
        self._current_price: float|None = None
        self._prev_price: float|None = None
        self._weebhook: DiscordWebhook = DiscordWebhook(
            webhook_url=webhook_url,
            username="Price Alert Bot",
        )
        self._subject = subject

    def get_handlers(self) -> dict[str, MessageHandlerCallback]:
        return {
            self._subject: self.on_ohlcv,
        }
    
    async def on_ohlcv(self, data: dict[str, Any]) -> None:
        logger.info(f"Received ohlcv data: {data}")
        if self._current_price is None or self._prev_price is None:
            self._prev_price = data["close"]
            self._current_price = data["close"]
        else:
            self._current_price = data["close"]
            prev = bisect.bisect_left(self._price_threshold, self._prev_price)
            curr = bisect.bisect_left(self._price_threshold, self._current_price)
            if prev != curr:
                if prev < curr:
                    logger.info(f"Price alert: {self._current_price} > {self._price_threshold[prev]}")
                else:
                    logger.info(f"Price alert: {self._current_price} < {self._price_threshold[curr]}")
                await self._weebhook.send_price_alert(
                    symbol=data["symbol"],
                    price=self._current_price,
                    threshold=self._price_threshold[prev] if prev < curr else self._price_threshold[curr],
                    condition="above" if prev < curr else "below"
                )
            self._prev_price = self._current_price
            


    

    