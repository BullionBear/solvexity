import pandas as pd
from solvexity.strategy.model.bar import Bar
from solvexity.agent.agent import Agent

class Bouncing:
    def __init__(self, 
        n_periods: int, 
        drawdown: float, # 0.01 = 1%, always positive
        springback: float, # 0.01 = 1%, always positive
        agent: Agent
    ):
        # Strategy Configuration
        self.n_periods = n_periods
        self.drawdown = drawdown
        self.springback = springback
        self.cooldown = 0

        # Strategy State
        self.bars: list[Bar] = []

        # Agent
        self.agent = agent


    async def on_bar(self, bar: Bar) -> bool:
        self.bars.append(bar)
        if len(self.bars) < self.n_periods:
            return False
        
        df_bars = pd.DataFrame([bar.to_dict() for bar in self.bars])
        df_bars['drawdown'] = df_bars['close'].rolling(window=self.n_periods).min()
        df_bars['springback'] = df_bars['close'].rolling(window=self.n_periods).max()
        df_bars['bouncing'] = df_bars['close'] > df_bars['drawdown'] and df_bars['close'] < df_bars['springback']
        return df_bars['bouncing'].iloc[-1]