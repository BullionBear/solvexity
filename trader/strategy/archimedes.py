import os
from typing import Type
from trader.core import Strategy
import helper.logging as logging

logger = logging.getLogger("trading")

class Archimedes(Strategy):
    def __init__(self, trade_id: str):
        super().__init__(trade_id)
        