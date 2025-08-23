from abc import ABC, abstractmethod

class Agent(ABC):
    @abstractmethod
    async def buy(self) -> str:
        pass

    @abstractmethod
    async def sell(self) -> str:
        pass

    @abstractmethod
    async def exit(self) -> str:
        pass

    
    