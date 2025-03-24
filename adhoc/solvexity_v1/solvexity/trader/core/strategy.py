from abc import ABC, abstractmethod
from typing import Optional
import solvexity.helper as helper


class Strategy(ABC):
    def __init__(self, trade_id: Optional[str] = None):
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

