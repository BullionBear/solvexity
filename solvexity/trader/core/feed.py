from abc import ABC, abstractmethod
from typing import Iterable
from solvexity.trader.model import KLine

class Feed(ABC):
    @abstractmethod
    def time(self)->int:
        pass

    @abstractmethod
    def send(self)->Iterable:
        pass

    @abstractmethod
    def receive(self, granular: str)->Iterable:
        pass
    
    @abstractmethod
    def get_klines(self, start: int, end: int, symbol: str, granular: str) -> list[KLine]:
        """
        The klines data is acsendingly ordered by the open time.
        """
        pass

    @abstractmethod
    def latest_n_klines(self, symbol: str, granular: str, limit: int) -> list[KLine]:
        """
        The klines data is acsendingly ordered by the open time.
        """
        pass

    @abstractmethod
    def close(self):
        pass
    