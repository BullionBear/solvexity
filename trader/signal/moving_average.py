from trader.core import Signal, SignalType

class MovingAverage(Signal):
    def __init__(self, trade_context, fast_period: int, slow_period: int, limit: int):
        super().__init__(trade_context)
        self.fast_period = fast_period
        self.slow_period = slow_period

    def solve(self):
        return SignalType.HOLD
    
    def export(self, destination: str):
        pass

    def visualize(self, destination: str):
        pass
    