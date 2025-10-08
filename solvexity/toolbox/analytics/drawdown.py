from .analytics import Analytics
import pandas as pd

class Drawdown(Analytics):
    """
    Calculate the drawdown of a given column.
    Drawdown is a positive value, the lower the better.
    """
    def __init__(self, src_col: str):
        self.src_col = src_col
        self.df = None
    
    def on_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        dataframe[f"{self.src_col}.cummax"] = dataframe[self.src_col].cummax()
        dataframe[f"{self.src_col}.drawdown"] = dataframe[f"{self.src_col}.cummax"] - dataframe[self.src_col]
        dataframe[f"{self.src_col}.drawdown_pct"] = dataframe[f"{self.src_col}.drawdown"] / dataframe[f"{self.src_col}.cummax"]
        
        return dataframe