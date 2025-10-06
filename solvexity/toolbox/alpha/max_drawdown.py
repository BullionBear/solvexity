from .analytics import Analytics
import pandas as pd
from typing import Callable

class MaxDrawdown(Analytics):
    def __init__(self, src_col: str):
        self.src_col = src_col
    
    def on_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        dataframe[f"{self.src_col}.cummax"] = dataframe[self.src_col].cummax()
        dataframe[f"{self.src_col}.drawdown"] = dataframe[self.src_col] - dataframe[f"{self.src_col}.cummax"]
        dataframe[f"{self.src_col}.drawdown_pct"] = dataframe[f"{self.src_col}.drawdown"] / dataframe[f"{self.src_col}.cummax"]
        dataframe[f"{self.src_col}.drawdown_pct"] = dataframe[f"{self.src_col}.drawdown_pct"].max()
        return dataframe