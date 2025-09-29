from typing import Callable
import pandas as pd
from solvexity.model.trade import Trade
from solvexity.eventbus.eventbus import EventBus
    


class DataframeAnalytics:
    def __init__(self, composers: list[Callable[[pd.DataFrame], pd.DataFrame]], eventbus: EventBus):
        self.composers = composers
        

    def on_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        for composer in self.composers:
            dataframe = composer(dataframe)
        return dataframe