import pandas as pd
from solvexity.model.strategy.bar import Bar
import logging
from solvexity.agent.agent import Agent

class CrossoverMA:
    def __init__(self, short_period: int, long_period: int, agent: Agent):
        # System
        self.bars: list[Bar] = []
        # Strategy
        self.short_period: int = short_period
        self.long_period: int = long_period
        # Agent
        self.agent: Agent = agent

    async def on_bar(self, bar: Bar) -> bool:
        self.bars.append(bar)
        if len(self.bars) < self.long_period:
            logging.info(f"Not enough bars to calculate crossover: {len(self.bars)} < {self.long_period}")

        df_bars = pd.DataFrame([bar.to_dict() for bar in self.bars])
        df_bars['short_period'] = df_bars['close'].rolling(window=self.short_period).mean()
        df_bars['long_period'] = df_bars['close'].rolling(window=self.long_period).mean()
        df_bars['crossover'] = df_bars['short_period'] > df_bars['long_period']
        return df_bars['crossover'].iloc[-1]


    
