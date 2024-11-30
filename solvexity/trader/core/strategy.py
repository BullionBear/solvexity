from abc import ABC, abstractmethod
from solvexity.trader.data import KLine

import solvexity.helper


class Strategy(ABC):
    def __init__(self, trade_id: str = None):
        if trade_id:
            self._id = trade_id
        else:
            self._id = helper.generate_random_id()


    @abstractmethod
    def invoke(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @property
    def id(self):
        return self._id

