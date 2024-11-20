
from typing import Type
from trader.core import TradeContext
from trader.core import Signal, SignalType
import helper.logging as logging
import pandas as pd

logger = logging.getLogger("trading")

pd.options.mode.copy_on_write = True

class DoublyMovingAverage(Signal):
    NAME = "Double Moving Average"
    def __init__(self, trade_context: Type[TradeContext], symbol: str, fast_period: int, slow_period: int, limit: int):
        super().__init__(trade_context)
        self.symbol = symbol
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.limit = limit

    def solve(self) -> SignalType:
        # Retrieve historical market data
        klines = self.trade_context.get_klines(self.symbol, self.limit)
        df = Signal.to_dataframe(klines)
        
        # Analyze the data to calculate moving averages
        df_analyze = self.analyze(df)
        
        # Check if there are enough data points for analysis
        if len(df_analyze) < 2:
            return SignalType.HOLD
        
        # Get the last two rows to determine the latest and previous values
        last_row = df_analyze.iloc[-1]
        previous_row = df_analyze.iloc[-2]

        # Check for a cross-over
        if last_row['fast'] > last_row['slow'] and previous_row['fast'] <= previous_row['slow']:
            return SignalType.BUY  # Fast line crossed above the slow line
        elif last_row['fast'] < last_row['slow'] and previous_row['fast'] >= previous_row['slow']:
            return SignalType.SELL  # Fast line crossed below the slow line
        else:
            return SignalType.HOLD  # No significant crossover
    
    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        df_analyze = df.copy()
        df_analyze['fast'] = df_analyze['close'].rolling(window=self.fast_period).mean()
        df_analyze['slow'] = df_analyze['close'].rolling(window=self.slow_period).mean()
        return df_analyze
        
    
    def export(self, df: pd.DataFrame, output_path: str):
        if not Signal.path_validator(output_path, 'csv'):
            logger.error(f"Invalid output csv path: {output_path}")
            return
        df.to_csv(output_path, index=False)

        

    def visualize(self, df: pd.DataFrame, output_path: str):
        if not Signal.path_validator(output_path, 'png'):
            logger.error(f"Invalid output png path: {output_path}")
            return
        import mplfinance as mpf

        ohlc_data = df[['open_time', 'open', 'high', 'low', 'close', 'quote_asset_volume']]
        ohlc_data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'quote_asset_volume': 'Volume'}, inplace=True)

        ohlc_data['open_time'] = pd.to_datetime(ohlc_data['open_time'], unit='ms')
        ohlc_data.set_index('open_time', inplace=True)

        mpf.plot(
            ohlc_data,
            type='candle',
            volume=True,
            style='charles',
            title='Candlestick Chart with Volume',
            ylabel='Price',
            ylabel_lower='Volume',
            mav=(5, 10),  # Moving averages
            figsize=(12, 8),
            show_nontrading=True,
            savefig=output_path
        )

