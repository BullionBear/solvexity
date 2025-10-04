import logging
import pandas as pd
from typing import Callable

logger = logging.getLogger(__name__)

class Analytics:
    def __init__(self, name: str, func: Callable[[pd.DataFrame], pd.DataFrame], result_to: str):
        self.name = name
        self.func = func
        self.result_to = result_to
    
    def on_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        dataframe = self.func(dataframe)
        return dataframe