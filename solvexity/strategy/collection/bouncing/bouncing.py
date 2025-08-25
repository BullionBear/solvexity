import pandas as pd
from solvexity.strategy.model.bar import Bar
from solvexity.agent.agent import Agent
import logging
from dataclasses import dataclass
from datetime import datetime


logger = logging.getLogger(__name__)

@dataclass
class BouncingResult:
    acc_max_px: float
    drawdown_px: float
    drawdown_time: datetime
    start_time: datetime
    end_time: datetime
    current_px: float

    def max_drawdown_pct(self) -> float:
        return (self.acc_max_px - self.drawdown_px) / self.acc_max_px

    def bouncing_pct(self) -> float:
        return (self.current_px - self.drawdown_px) / self.drawdown_px


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
        # Strategy State
        self.bars: list[Bar] = []

        # Agent
        self.agent = agent


    async def on_bar(self, bar: Bar):
        self.bars.append(bar)
        if len(self.bars) < self.n_periods:
            return False
        
        df_bars = pd.DataFrame([bar.to_dict() for bar in self.bars])
        bouncing_result = self.calculate_bouncing(df_bars)
        if bouncing_result.max_drawdown_pct() > self.drawdown and bouncing_result.bouncing_pct() > self.springback:
            return await self.agent.enter()
        
        

    def calculate_bouncing(self, df_bars: pd.DataFrame) -> BouncingResult:
        df_high = df_bars.copy()
        df_low = df_bars.copy()

        df_high['ref_flag'] = df_bars['close'] - df_bars['low'] > df_bars['high'] - df_bars['close']
        df_low['ref_flag'] = ~df_high['ref_flag']
        # Determine if close price is closer to high or low
        df_high['ref_flag'] = df_bars['close'] - df_bars['low'] > df_bars['high'] - df_bars['close']
        df_low['ref_flag'] = ~df_high['ref_flag']
        
        # Set reference prices
        df_high['ref_price'] = df_bars['high']
        df_low['ref_price'] = df_bars['low']
        
        # Merge high and low dataframes
        df_merge = pd.concat([df_high, df_low], axis=0)
        df_merge.sort_values(['open_time', 'ref_flag'], kind='mergesort', inplace=True)
        df_merge.reset_index(drop=True, inplace=True)
        
        # Calculate cumulative maximum and drawdown
        df_merge["acc_max"] = df_merge["ref_price"].cummax()
        df_merge["drawdown"] = df_merge["acc_max"] - df_merge["ref_price"]
        df_merge["drawdown_pct"] = df_merge["drawdown"] / df_merge["acc_max"]
        
        # Sort by drawdown and remove duplicates
        df_merge.sort_values('drawdown', inplace=True, ascending=False)
        df_merge.drop_duplicates(subset='open_time', keep='first', inplace=True)
        df_merge.sort_values('open_time', inplace=True)
        df_merge.reset_index(drop=True, inplace=True)

        end_idx = df_merge['drawdown'].idxmax()
        if end_idx == 0:
            logger.warning("Maximal Drawdown ended up with first index.")
            return

        start_idx = df_merge.iloc[:end_idx]['ref_price'].idxmax()
        
        max_drawdown = df_merge['drawdown_pct'].max()
        start_time = pd.to_datetime(df_merge.iloc[start_idx]['open_time'], unit='ms')
        end_time = pd.to_datetime(df_merge.iloc[end_idx]['open_time'], unit='ms')
        logger.info(f"Maximal Drawdown: {max_drawdown:.2%}, Start Time: {start_time}, End Time: {end_time}")
        return BouncingResult(
            acc_max_px=df_merge.iloc[end_idx]['acc_max'],
            drawdown_px=df_merge.iloc[end_idx]['drawdown'],
            drawdown_time=start_time,
            start_time=start_time,
            end_time=df_bars.iloc[-1]['close_time'],
            current_px=df_bars.iloc[-1]['close'],
        )
        
        
        

        