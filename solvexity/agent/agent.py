from abc import ABC, abstractmethod

class Agent(ABC):

    @abstractmethod
    async def enter(self) -> str:
        pass

    @abstractmethod
    async def exit(self) -> str:
        pass

    @abstractmethod
    async def reverse(self) -> str:
        pass
    