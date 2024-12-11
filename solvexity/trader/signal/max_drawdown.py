
import os
from typing import Type
from solvexity.trader.core import TradeContext
from solvexity.trader.core import Signal, SignalType
import solvexity.helper.logging as logging
import pandas as pd

logger = logging.getLogger()

pd.options.mode.copy_on_write = True

class MaxDrawdown(Signal):
    """
    In Bullish markets, the drawdown is the percentage decline from the peak, a period of drawdown is the good time to buy.
    MaxDrawdown only return HOLD and BUY signals.
    """
    NAME = "Maximal Drawdown"
    def __init__(self, trade_context: Type[TradeContext], symbol: str, rollback_period: int, threshold: float, granular: str):
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
        # Analyze the data to calculate moving averages
        self.df_analyze = self.analyze(df)
        return SignalType.BUY

    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        if len(df) < self.rollback_period:
            logger.warning(f"Insufficient data points for analysis. Expected at least {self.slow_period} but receive {len(df)}.")
            return df
        df_analyze = df.copy()
        high_data = df_analyze[['open_time', 'high']].copy()
        high_data['is_high'] = True
        high_data.rename(columns={'high': 'price'}, inplace=True)
        low_data = df_analyze[['open_time', 'low']].copy()
        low_data['is_high'] = False
        low_data.rename(columns={'low': 'price'}, inplace=True)
        transformed_df = pd.concat([high_data, low_data], axis=0)
        transformed_df.sort_values(by=['open_time', 'is_high'], ascending=[True, False], inplace=True)
        transformed_df['cumulative_max'] = transformed_df['price'].cummax()
        transformed_df['drawdown'] = (transformed_df['cumulative_max'] - transformed_df['price']) / transformed_df['cumulative_max']

        df_analyze['fast'] = df_analyze['close'].rolling(window=self.fast_period).mean()
        df_analyze['slow'] = df_analyze['close'].rolling(window=self.slow_period).mean()
        return df_analyze
    
    def get_filename(self) -> str:
        latest_time = self.df_analyze.iloc[-1].open_time
        return f"{self.symbol}_{latest_time}"
        
    
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
        
