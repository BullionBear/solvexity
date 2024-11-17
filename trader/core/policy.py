from typing import Type
from abc import ABC, abstractmethod
from .trade_context import TradeContext

class Policy(ABC):
    """
        A policy is a set of rules that governs the behavior of a trading bot.
    """
    def __init__(self, trade_context: Type[TradeContext]):
        self.trade_context = trade_context
    
    @abstractmethod
    def buy(self):
        pass
    
    @abstractmethod
    def sell(self):
        pass