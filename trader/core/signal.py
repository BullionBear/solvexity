from typing import Type
from abc import ABC, abstractmethod
from trader.data import KLine
from .trade_context import TradeContext
import enum

class SignalType(enum.Enum):
    BUY = 'BUY'
    HOLD = 'HOLD'
    SELL = 'SELL'

class Signal(ABC):
    """
        A policy is a set of rules that governs the behavior of a trading bot.
    """
    def __init__(self, trade_context: Type[TradeContext]):
        self.trade_context = trade_context
    
    @abstractmethod
    def solve(self, klines: list[KLine]) -> SignalType:
        pass