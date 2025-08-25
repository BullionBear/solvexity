from abc import ABC, abstractmethod

class Agent(ABC):
    @abstractmethod
    async def enter(self):
        pass

    @abstractmethod
    async def exit(self):
        pass

    @abstractmethod
    async def reverse(self):
        pass

    async def subscribe(self):
        pass
