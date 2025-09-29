from solvexity.model.trade import Trade
from .trigger import DataframeTrigger
from .analytics import DataframeAnalytics
from solvexity.eventbus.eventbus import EventBus


class Pipeline:
    def __init__(self, eventbus: EventBus, trigger: DataframeTrigger, analytics: DataframeAnalytics):
        self.eventbus = eventbus
        self.eventbus.subscribe("on_trade", lambda e: trigger.on_trade(e.data))
        self.eventbus.subscribe("on_dataframe", lambda e: analytics.on_dataframe(e.data))