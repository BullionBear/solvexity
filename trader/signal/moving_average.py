from trader.core import Signal, SignalType

class MovingAverageSignal(Signal):
    def __init__(self, trade_context, symbol: str, grandular: str, fast_period: int, slow_period: int, limit: int):
        super().__init__(trade_context)
        self.symbol = symbol
        self.grandular = grandular
        self.fast_period = fast_period
        self.slow_period = slow_period

    def solve(self):
        klines = self.trade_context.get_klines(self.symbol, self.limit)
        return SignalType.HOLD
    
    def export(self, destination: str):
        pass

    def visualize(self, destination: str):
        pass
    