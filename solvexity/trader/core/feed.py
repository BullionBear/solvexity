from abc import ABC, abstractmethod
from typing import Iterable
from solvexity.trader.model import KLine

class Feed(ABC):
    @abstractmethod
    def send()->Iterable:
        pass

    @abstractmethod
    def receive()->Iterable:
        pass

    @abstractmethod
    def get_klines(start: int, end: int, symbol: str, granular: str) -> list[KLine]:
        pass

    @abstractmethod
    def close():
        pass
    