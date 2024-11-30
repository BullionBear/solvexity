from typing import Type
from dependency.notification import Color
from abc import ABC, abstractmethod
from .trade_context import TradeContext
import helper

class Policy(ABC):
    """
        A policy is a set of rules that governs the behavior of a trading bot.
    """
    def __init__(self, trade_context: Type[TradeContext], trade_id: str):
        if trade_id:
            self._id = trade_id
        else:
            self._id = helper.generate_random_id()
        self.trade_context = trade_context  

    @abstractmethod
    def buy(self):
        pass
    
    @abstractmethod
    def sell(self):
        pass

    def notify(self, title: str, content: str, color: Color):
        self.trade_context.notify(self.id, title, content, color)

    @abstractmethod
    def export(self, output_dir: str):
        pass

    @property
    def id(self):
        return self._id

    

