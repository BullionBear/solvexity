from solvexity.model.trade import Trade
from .trigger import DataframeTrigger
from solvexity.eventbus.eventbus import EventBus


class Pipeline:
    def __init__(self, eventbus: EventBus, trigger: DataframeTrigger):
        self.eventbus = eventbus
        self.trigger = trigger

    async def on_trade(self, trade: Trade):
        await self.trigger.on_trade(trade)
