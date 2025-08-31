import logging
from solvexity.model.bar import Bar

logger = logging.getLogger(__name__)

class Bouncing:
    def __init__(self, n_periods: int, drawdown: float, springback: float):
        self.n_periods = n_periods
        self.drawdown = drawdown
        self.springback = springback
        self.bars: list[Bar] = []

    async def start(self):
        pass

    async def stop(self):
        pass

    async def on_bar(self, bar: Bar):
        logger.info(f" On bar: {bar}")
