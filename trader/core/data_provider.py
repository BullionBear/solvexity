from abc import ABC, abstractmethod

class DataProvider(ABC):
    @abstractmethod
    def send():
        pass

    @abstractmethod
    def receive():
        pass

    