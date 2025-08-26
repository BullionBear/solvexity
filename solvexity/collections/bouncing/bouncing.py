from solvexity.model.bar import Bar
from solvexity.collections.factory import StrategyFactory
from solvexity.strategy.strategy import Strategy

class Bouncing(Strategy):
    def __init__(self):
        self.bars: list[Bar] = []

    async def on_bar(self, bar: Bar):
        self.bars.append(bar)

StrategyFactory.register("bouncing", Bouncing)