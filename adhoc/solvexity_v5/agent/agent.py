from abc import ABC, abstractmethod


class Agent(ABC):
    @abstractmethod
    async def enter(self):
        pass

    @abstractmethod
    async def exit(self):
        pass