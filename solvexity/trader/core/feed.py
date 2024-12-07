from abc import ABC, abstractmethod
from typing import Iterable
from solvexity.trader.model import KLine

class Feed(ABC):
    @abstractmethod
    def time()->int:
        pass

    @abstractmethod
    def send()->Iterable:
        pass

    @abstractmethod
    def receive(granular: str)->Iterable:
        pass
    
    @abstractmethod
    def get_klines(start: int, end: int, symbol: str, granular: str) -> list[KLine]:
        """
        The klines data is acsendingly ordered by the open time.
        """
        pass

    @abstractmethod
    def latest_n_klines(symbol: str, granular: str, limit: int) -> list[KLine]:
        """
        The klines data is acsendingly ordered by the open time.
        """
        pass

    @abstractmethod
    def close():
        pass
    