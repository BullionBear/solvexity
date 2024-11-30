import os
from typing import Type
from abc import ABC, abstractmethod
from solvexity.trader.data import KLine
from .trade_context import TradeContext
import solvexity.helper.logging as logging
import pandas as pd
import enum

logger = logging.getLogger("trading")

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

    def get_context(self) -> Type[TradeContext]:
        return self.trade_context

    @staticmethod
    def to_dataframe(data: list[KLine]):
        data_dict = [kline.model_dump() for kline in data]
        return pd.DataFrame(data_dict)
    
    @staticmethod
    def directory_validator(directory: str) -> bool:
        """
        Validates a directory path.
    
        Args:
            directory (str): The directory path to validate.
    
        Returns:
            bool: True if the path is a valid directory, False otherwise.
        """
        if not directory:
            logger.error("Error: The directory path is empty.")
            return False
        
        if not os.path.exists(directory):
            logger.error(f"Error: The directory '{directory}' does not exist.")
            return False
        
        if not os.path.isdir(directory):
            logger.error(f"Error: The path '{directory}' is not a directory.")
            return False
    
        return True