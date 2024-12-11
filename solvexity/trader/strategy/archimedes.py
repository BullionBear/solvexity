import os
from typing import Type
from solvexity.trader.core import Strategy
import solvexity.helper.logging as logging

logger = logging.getLogger()

class Archimedes(Strategy):
    def __init__(self, trade_id: str):
        super().__init__(trade_id)
        