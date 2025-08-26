from abc import ABC, abstractmethod
from typing import Any, Callable



class Feed(ABC):
    @abstractmethod
    def subscribe(self, callback: Callable[[Any], None]) -> Callable[[], None]:
        pass

