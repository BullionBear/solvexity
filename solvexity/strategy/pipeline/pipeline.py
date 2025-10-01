from solvexity.model.trade import Trade
from .trigger import DataframeTrigger
from .analytics import DataframeAnalytics
from solvexity.eventbus.eventbus import EventBus
from solvexity.eventbus.event import Event


class Pipeline:
    def __init__(self, trigger: DataframeTrigger, analytics: DataframeAnalytics):
        self.eventbus = EventBus()
        self.trigger = trigger
        self.analytics = analytics
        self.eventbus.subscribe("on_trade", self.publish_to_trigger)
        self.eventbus.subscribe("on_dataframe", lambda e: analytics.on_dataframe(e.data))
    
    async def publish_to(self, event: Event):
        await self.trigger.on_trade(event.data)
        if self.trigger.size() > self.trigger.buf_size:
            await self.analytics.on_dataframe(self.trigger.last(closed=True))
        