from .feed import Feed

class Solver:
    def __init__(self, feed: Feed):
        self.feed = feed

    def solve(self, symbol: str, timestamp: int):
        df_15m = self.feed.get_klines(symbol, "15m", timestamp - 86400_000, timestamp)
        print("solve 15m")
        df_15m.to_csv(f"verbose/15m_{symbol}_{timestamp}.csv", index=False)


