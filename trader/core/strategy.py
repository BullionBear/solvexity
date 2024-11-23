from abc import ABC, abstractmethod
from trader.data import KLine

import helper


class Strategy(ABC):
    def __init__(self, trade_id: str = None):
        if trade_id:
            self._id = trade_id
        else:
            self._id = helper.generate_random_id()


    @abstractmethod
    def invoke(self):
        pass

    @property
    def id(self):
        return self._id

