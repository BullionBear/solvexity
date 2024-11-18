from trader.core import Signal, SignalType
import pandas as pd

pd.options.mode.copy_on_write = True


class DoubleMovingAverage(Signal):
    def __init__(self, trade_context, symbol: str, fast_period: int, slow_period: int, limit: int):
        super().__init__(trade_context)
        self.symbol = symbol
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.limit = limit

    def solve(self):
        klines = self.trade_context.get_klines(self.symbol, self.limit)
        df = Signal.to_dataframe(klines)
        self.analyze(df)
        return SignalType.HOLD
    
    def analyze(self, df: pd.DataFrame) -> pd.DataFrame:
        df['fast'] = df['close'].rolling(window=self.fast_period).mean()
        df['slow'] = df['close'].rolling(window=self.slow_period).mean()
        pass
    
    def export(self, destination: str):
        pass

    def visualize(self, destination: str):
        pass
