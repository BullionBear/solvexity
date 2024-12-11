
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
        mdd = self.analyze(df)
        if mdd > self.threshold:
            return SignalType.BUY
        return SignalType.HOLD

    def analyze(self, df: pd.DataFrame) -> float:
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
        self.df_analyze = transformed_df
        mdd, _, _ = MaxDrawdown.max_drawdown(transformed_df['price'].values)
        return mdd
    
    def get_filename(self) -> str:
        latest_time = self.df_analyze.iloc[-1].open_time
        return f"{self.symbol}_{latest_time}_MDD"
    
    @staticmethod
    def max_drawdown(prices):
        """
        Calculate the Maximum Drawdown (MDD) of a list of prices.

        Args:
            prices (list or array-like): A list of prices (e.g., stock prices).

        Returns:
            float: The maximum drawdown as a percentage.
            tuple: The indices of the peak and the trough during the max drawdown.
        """
        if len(prices) < 2:
            return 0, None

        peak = prices[0]
        max_dd = 0
        peak_index = 0
        through_index = 0
        current_peak_index = 0

        for i in range(1, len(prices)):
            if prices[i] > peak:
                peak = prices[i]
                current_peak_index = i
            drawdown = (peak - prices[i]) / peak
            if drawdown > max_dd:
                max_dd = drawdown
                peak_index = current_peak_index
                through_index = i
        return max_dd * 100, (peak_index, through_index)
        
    
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
            figsize=(12, 8),
            show_nontrading=True,
            savefig=target_dest
        )
        logger.info(f"Exported visualization to {target_dest}")
        
