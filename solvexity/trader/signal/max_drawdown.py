
import os
from typing import Type
from solvexity.trader.core import TradeContext
from solvexity.trader.core import Signal, SignalType
import solvexity.helper.logging as logging
import mplfinance as mpf
import matplotlib
import pandas as pd

logger = logging.getLogger()

pd.options.mode.copy_on_write = True

class MaxDrawdown(Signal):
    """
    In Bullish markets, the drawdown is the percentage decline from the peak, a period of drawdown is the good time to buy.
    MaxDrawdown only return HOLD and BUY signals.
    Assume max drawdown is positive, for example, 10% max drawdown is 0.1
    """
    NAME = "Maximal Drawdown"
    def __init__(self, trade_context: Type[TradeContext], symbol: str, rollback_period: int, threshold: float, granular: str):
        super().__init__(trade_context)
        self.symbol: str = symbol
        self.rollback_period: int = rollback_period
        self.granular: str = granular
        self.threshold: float = threshold

        self.df_analyze: pd.DataFrame = None
        self._cache_range = []

    def solve(self) -> SignalType:
        # Retrieve historical market data
        klines = self.trade_context.get_klines(self.symbol, self.rollback_period, self.granular)
        df = Signal.to_dataframe(klines)
        # Analyze the data to calculate moving averages
        mdd, start_time, end_time = self.analyze(df)
        logger.info(f"Maximal Drawdown: {mdd} from {start_time} to {end_time}")
        if start_time == end_time:
            return SignalType.HOLD
        if mdd < self.threshold:
            return SignalType.HOLD
        for c_start, c_end in self._cache_range:
            if c_start <= start_time <= c_end or c_start <= end_time <= c_end:
                logger.info(f"Maximal Drawdown signal is overlayed. Start: {c_start}, End: {c_end}")
                return SignalType.HOLD
        self._cache_range.append((start_time, end_time))
        return SignalType.BUY

    def analyze(self, df: pd.DataFrame) -> tuple[float, int, int]:
        if len(df) < self.rollback_period:
            logger.warning(f"Insufficient data points for analysis. Expected at least {self.slow_period} but receive {len(df)}.")
            return 0.0, 0, 0
        self.df_analyze = MaxDrawdown.drawdown(df)
        end_idx = self.df_analyze['drawdown'].idxmax()
        start_idx = self.df_analyze.iloc[:end_idx]['ref_price'].idxmax()

        return self.df_analyze['drawdown_pct'].max(), self.df_analyze.iloc[start_idx].open_time, self.df_analyze.iloc[end_idx].open_time
    
    def get_filename(self) -> str:
        latest_time = self.df_analyze.iloc[-1].open_time
        return f"{self.symbol}_{latest_time}_MDD"
    
    @staticmethod
    def drawdown(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate the Maximum Drawdown (MDD) from kline dataframe.
        """
        df_high = df.copy()
        df_low = df.copy()
        df_high['ref_flag'] = df['close'] - df['low'] > df['high'] - df['close']
        df_low['ref_flag'] = ~df_high['ref_flag']
        df_high['ref_price'] = df['high']
        df_low['ref_price'] = df['low']
        df_merge = pd.concat([df_high, df_low], axis=0)
        df_merge.sort_values(['open_time', 'ref_flag'], kind='mergesort', inplace=True)
        df_merge.reset_index(drop=True, inplace=True)
        df_merge["acc_max"] = df_merge["ref_price"].cummax()
        df_merge["drawdown"] = df_merge["acc_max"] - df_merge["ref_price"]
        df_merge["drawdown_pct"] = df_merge["drawdown"] / df_merge["acc_max"]
        df_merge.sort_values('drawdown', inplace=True, ascending=False)
        df_merge.drop_duplicates(subset='open_time', keep='first', inplace=True)
        df_merge.sort_values('open_time', inplace=True)
        return df_merge
        
    
    def export(self, output_dir: str):
        if not Signal.directory_validator(output_dir):
            return
        target_dest = os.path.join(output_dir, f"{self.get_filename()}.csv")
        self.df_analyze.to_csv(target_dest, index=False)
        logger.info(f"Exported analysis data to {target_dest}")

    def visualize(self, output_dir: str):
        if not Signal.directory_validator(output_dir):
            return
        matplotlib.use('Agg')  # Ensure a non-GUI backend is used
        ohlc_data = self.df_analyze[['open_time', 'open', 'high', 'low', 'close', 'quote_asset_volume']]
        ohlc_data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'quote_asset_volume': 'Volume'}, inplace=True)

        ohlc_data['open_time'] = pd.to_datetime(ohlc_data['open_time'], unit='ms')
        ohlc_data.set_index('open_time', inplace=True)
        target_dest = os.path.join(output_dir, f"{self.get_filename()}.png")
        additional_lines = [
        mpf.make_addplot(ohlc_data['acc_max'], color='green', width=1.5, linestyle='dotted', ylabel="acc_max"),
        mpf.make_addplot(ohlc_data['acc_max'] - ohlc_data['drawdown'], color='orange', width=1.5, linestyle='dashed', ylabel="acc_max - drawdown")
        ]
        mpf.plot(
            ohlc_data,
            type='candle',
            volume=True,
            style='charles',
            title='Candlestick Chart with Volume',
            ylabel='Price',
            ylabel_lower='Volume',
            addplot=additional_lines,
            figsize=(12, 8),
            show_nontrading=True,
        )
        logger.info(f"Exported visualization to {target_dest}")
        
