from typing import Any
import bisect
from solvexity.alert import DiscordWebhook
from hooklet.base import BasePilot
from hooklet.eventrix.handler import Handler
from hooklet.types import MessageHandlerCallback

class OCHLVPriceAlert(Handler):
    def __init__(self, pilot: BasePilot, twap_amount: float, symbol: str, interval: int, subject: str, executor_id: str|None = None):
        super().__init__(pilot, executor_id)
        self._twap_amount = twap_amount
        self._symbol = symbol
        self._interval = interval
        self._current_price: float|None = None
        self._prev_price: float|None = None
        self._subject = subject

    