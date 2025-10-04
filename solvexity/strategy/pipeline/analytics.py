import logging
from typing import Callable
import pandas as pd
from solvexity.model.trade import Trade
from solvexity.eventbus.eventbus import EventBus
from solvexity.eventbus.event import Event

logger = logging.getLogger(__name__)
    
class Analytics:
    def __init__(self, name: str, func: Callable[[pd.DataFrame], pd.DataFrame], result_to: str):
        self.name = name
        self.func = func
        self.result_to = result_to
    
    def on_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        dataframe = self.func(dataframe)
        return dataframe

class DataframeAnalytics:
    def __init__(self, composers: list[Analytics]):
        self.composers = composers
        self.eventbus = EventBus()
        for composer in self.composers:
            self.eventbus.subscribe(composer.name, composer.on_dataframe)
        

    def on_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        for composer in self.composers:
            dataframe = composer.on_dataframe(dataframe)
            self.eventbus.publish(composer.result_to, Event(data=dataframe))
        return dataframe