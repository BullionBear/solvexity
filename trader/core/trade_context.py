class TradeContext:
    def __init__(self):
        pass

class BacktestContext(TradeContext):
    def __init__(self):
        pass

class PaperTradeContext(TradeContext):
    def __init__(self):
        pass

class LiveTradeContext(TradeContext):
    def __init__(self):
        pass

class TradeContextFactory:
    @staticmethod
    def create():
        return TradeContext()