import pandas as pd
from solvexity.model.strategy import Bar

class Bouncing:
    def __init__(self, n_periods: int, drawdown: float, springback: float):
        self.n_periods = n_periods
        self.drawdown = drawdown
        self.springback = springback
        self.bars: list[Bar] = []

    async def on_bar(self, bar: Bar) -> bool:
        pass