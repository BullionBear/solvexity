from abc import ABC, abstractmethod
import logging
import pandas as pd
from typing import Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AlphaMetadata:
    author: str
    name: str
    description: str


class Alpha(ABC):
    def __init__(self, metadata: AlphaMetadata):
        self.metadata = metadata

    @abstractmethod
    def on_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        pass