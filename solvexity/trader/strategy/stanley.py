import os
from typing import Type
from solvexity.trader.core import Strategy
from solvexity.trader.core import Strategy, Signal, Policy, SignalType
from solvexity.trader.report import Report
import solvexity.helper.logging as logging

logger = logging.getLogger()

class Stanley(Strategy):
    def __init__(self, signal: Type[Signal], policy: Type[Policy], symbol: str, granular: str, trade_id: str, verbose: bool = False):
        super().__init__(trade_id)