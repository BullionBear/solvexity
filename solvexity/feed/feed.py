from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator


class Feed(ABC):
    @abstractmethod
    async def recv(self) -> AsyncGenerator[Any, None]:
        pass
