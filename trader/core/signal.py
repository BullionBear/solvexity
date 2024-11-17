from typing import Type
from abc import ABC, abstractmethod
from trader.data import KLine
from .trade_context import TradeContext
import pandas as pd
import enum

class SignalType(enum.Enum):
    BUY = 'BUY'
    HOLD = 'HOLD'
    SELL = 'SELL'

class Signal(ABC):
    """
        Trading signal generator.
    """
    def __init__(self, trade_context: Type[TradeContext]):
        self.trade_context = trade_context
    
    @abstractmethod
    def solve(self) -> SignalType:
        pass

    @abstractmethod
    def export(self, destination: str):
        pass

    @abstractmethod
    def visualize(self, destination: str):
        pass

    @staticmethod
    def to_dataframe(data: list[KLine]):
        data_dict = [kline.model_dump() for kline in data]
        return pd.DataFrame(data_dict)