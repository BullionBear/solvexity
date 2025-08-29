import logging
from solvexity.model.bar import Bar
from solvexity.collections.factory import StrategyFactory
from solvexity.strategy.strategy import Strategy
from solvexity.eventbus.event import Event

logger = logging.getLogger(__name__)

class Bouncing(Strategy):
    def __init__(self):
        self.bars: list[Bar] = []

    async def start(self):
        pass

    async def stop(self):
        pass

    async def on_bar(self, bar: Bar):
        logger.info(f" On bar: {bar}")
        self.bars.append(bar)

StrategyFactory.register("bouncing", Bouncing)