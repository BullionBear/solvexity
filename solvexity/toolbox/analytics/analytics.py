from abc import ABC, abstractmethod
import logging
import pandas as pd
from typing import Callable

logger = logging.getLogger(__name__)


class Analytics(ABC):
    @abstractmethod
    def on_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        pass
