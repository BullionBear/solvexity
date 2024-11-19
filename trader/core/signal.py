import os
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
    def export(self, output_dir: str):
        pass

    @abstractmethod
    def visualize(self, output_dir: str):
        pass

    @staticmethod
    def to_dataframe(data: list[KLine]):
        data_dict = [kline.model_dump() for kline in data]
        return pd.DataFrame(data_dict)
    
    @staticmethod
    def path_validator(self, output_path: str, extension: str):
        try:
            # Ensure the path ends with .png
            if not output_path.lower().endswith(f'.{extension}'):
                return False

            # Check if the directory exists
            directory = os.path.dirname(output_path)
            if directory and not os.path.exists(directory):
                return False

            # Check if we can write to the directory
            if directory and not os.access(directory, os.W_OK):
                return False

            # Check if the path does not contain invalid characters
            os.path.normpath(output_path)  # Raises an exception if the path is invalid
            return True
        except Exception:
            return False