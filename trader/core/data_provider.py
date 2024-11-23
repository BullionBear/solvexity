from abc import ABC, abstractmethod

class DataProvider(ABC):
    @abstractmethod
    def __next__(self):
        pass
    
    def __iter__(self):
        """Return an iterator for the data stream."""
        return self

    