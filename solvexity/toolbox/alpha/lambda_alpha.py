from .analytics import Analytics
from typing import Callable
import pandas as pd

class LambdaAnalytics(Analytics):
    def __init__(self, name: str, func: Callable[[pd.DataFrame], pd.DataFrame], result_to: str):
        self.name = name
        self.func = func
        self.result_to = result_to
    
    def on_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        return self.func(dataframe)