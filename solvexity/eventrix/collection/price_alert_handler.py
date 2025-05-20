import asyncio
import logging
from typing import Any
from hooklet.base import BasePilot
from hooklet.eventrix.handler import Handler
from hooklet.types import MessageHandlerCallback

logger = logging.getLogger(__name__)


class OCHLVPriceAlert(Handler):
    def __init__(self, pilot: BasePilot, price_thresholds: list[float], subject: str, executor_id: str|None = None):
        super().__init__(pilot, executor_id)
        self._price_alerts: list[float] = price_thresholds
        self._current_price: float|None = None
        self._subject = subject

    def get_handlers(self) -> dict[str, MessageHandlerCallback]:
        return {
            self._subject: self.on_ochlv,
        }
    
    async def on_ochlv(self, data: dict[str, Any]) -> None:
        logger.info(f"Received data: {data}")

    

    