
import os
from typing import Type
from solvexity.trader.core import TradeContext
from solvexity.trader.core import Signal, SignalType
import solvexity.helper.logging as logging
import pandas as pd

logger = logging.getLogger("trading")

pd.options.mode.copy_on_write = True

class MaxDrawdown(Signal):
    """
    In Bullish markets, the drawdown is the percentage decline from the peak, a period of drawdown is the good time to buy.
    MaxDrawdown only return HOLD and BUY signals.
    """
    NAME = "Max Drawdown"
    def __init__(self, trade_context: Type[TradeContext], symbol: str, rollback_period: int, granular: str, threshold: float):
        super().__init__(trade_context)
        self.symbol: str = symbol
        self.rollback_period: int = rollback_period
        self.granular: str = granular
        self.threshold: float = threshold

        self.df_analyze: pd.DataFrame = None

    def solve(self) -> SignalType:
        # Retrieve historical market data
        klines = self.trade_context.get_klines(self.symbol, self.rollback_period, self.granular)
        df = Signal.to_dataframe(klines)
        # Analyze the data to calculate max drawdown
        self.df_analyze = self.analyze(df)
        self.df_analyze.to_csv("max_drawdown.csv", index=False)
        max_drawdown = self.df_analyze['drawdown'].min()
        if max_drawdown < self.threshold:
            return SignalType.BUY
        return SignalType.HOLD

    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        if len(df) < self.rollback_period:
            logger.warning(f"Insufficient data points for analysis. Expected at least {self.rollback_period} but receive {len(df)}.")
            return df
        df_analyze = df.copy()
        # Convert open_time to a readable datetime format
        df_analyze['open_time'] = pd.to_datetime(df_analyze['open_time'], unit='ms')

        # Calculate the cumulative max using the high prices and drawdown using the low prices
        df_analyze['cumulative_high'] = df_analyze['high'].cummax()
        df_analyze['drawdown'] = (df_analyze['low'] - df_analyze['cumulative_high']) / df['cumulative_high']
        # Find the maximum drawdown
        # max_drawdown = df['drawdown'].min()
        # max_drawdown_row = df[df['drawdown'] == max_drawdown]

        # # Identify the start of the drawdown (max cumulative high before the drawdown)
        # drawdown_start_index = df.loc[:max_drawdown_row.index[0]]['high'].idxmax()
        # drawdown_start_time = df.loc[drawdown_start_index, 'open_time']

        # # Identify the end of the drawdown (minimum low during the drawdown period)
        # drawdown_end_time = max_drawdown_row['open_time'].iloc[0]

        # max_drawdown, drawdown_start_time, drawdown_end_time
        # return {
        #     "percentage": max_drawdown,
        #     "start": int(drawdown_start_time.timestamp() * 1000),
        #     "from": int(drawdown_end_time.timestamp() * 1000)
        # }

        return df_analyze
    
    def get_filename(self) -> str:
        latest_time = self.df_analyze.iloc[-1].open_time
        return f"{self.symbol}_{latest_time}_mdd"
        
    
    def export(self, output_dir: str):
        if not Signal.directory_validator(output_dir):
            return
        target_dest = os.path.join(output_dir, f"{self.get_filename()}.csv")
        self.df_analyze.to_csv(target_dest, index=False)
        logger.info(f"Exported analysis data to {target_dest}")

    def visualize(self, output_dir: str):
        if not Signal.directory_validator(output_dir):
            return
        import mplfinance as mpf

        ohlc_data = self.df_analyze[['open_time', 'open', 'high', 'low', 'close', 'quote_asset_volume']]
        ohlc_data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'quote_asset_volume': 'Volume'}, inplace=True)

        ohlc_data['open_time'] = pd.to_datetime(ohlc_data['open_time'], unit='ms')
        ohlc_data.set_index('open_time', inplace=True)
        target_dest = os.path.join(output_dir, f"{self.get_filename()}.png")
        mpf.plot(
            ohlc_data,
            type='candle',
            volume=True,
            style='charles',
            title='Candlestick Chart with Volume',
            ylabel='Price',
            ylabel_lower='Volume',
            mav=(self.fast_period, self.slow_period),  # Moving averages
            mavcolors=['red', 'blue'],  # Apply the custom colors here
            figsize=(12, 8),
            show_nontrading=True,
            savefig=target_dest
        )
        logger.info(f"Exported visualization to {target_dest}")
        
