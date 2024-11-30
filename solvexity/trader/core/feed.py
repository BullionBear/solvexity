from abc import ABC, abstractmethod

class Feed(ABC):
    @abstractmethod
    def send():
        pass

    @abstractmethod
    def receive():
        pass

    @abstractmethod
    def close():
        pass
    