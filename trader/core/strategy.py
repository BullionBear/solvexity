from typing import Type
from abc import ABC, abstractmethod
from trader.data import KLine
from trader.core import Policy, Signal, SignalType
from .trade_context import TradeContext
from decimal import Decimal
import helper

class Strategy(ABC):
    def __init__(self, trade_context: Type[TradeContext], trade_id: str = None):
        self.trade_context = trade_context
        if trade_id:
            self._id = trade_id
        else:
            self._id = helper.generate_random_id()


    @abstractmethod
    def invoke(self, klines: list[KLine]):
        pass

    def market_buy(self, symbol: str, size: Decimal):
        self.trade_context.market_buy(symbol, size)

    def market_sell(self, symbol: str, size: Decimal):
        self.trade_context.market_sell(symbol, size)

    def get_balance(self, token: str) -> Decimal:
        return self.trade_context.get_balance(token)
    
    def get_klines(self, symbol: str, limit: int) -> list[KLine]:
        return self.trade_context.get_klines(symbol, limit)
    
    def get_trades(self, symbol: str, limit: int):
        return self.trade_context.get_trades(symbol, limit)
    
    def notify(self, **kwargs):
        self.trade_context.notify(**kwargs)

class StrategyV2(ABC):
    def __init__(self, policy: Type[Policy], signal: Type[Signal], trade_id: str = None):
        self.policy = policy
        self.signal = signal
        if trade_id:
            self._id = trade_id
        else:
            self._id = helper.generate_random_id()
    
    @abstractmethod
    def invoke(self, klines: list[KLine]):
        pass
    