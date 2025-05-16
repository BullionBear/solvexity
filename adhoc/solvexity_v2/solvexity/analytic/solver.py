import pandas as pd
import matplotlib
matplotlib.use('Agg')
import mplfinance as mpf

from .feed import Feed
from .pattern import Pattern
from solvexity.helper import to_ms_interval

class Solver:
    def __init__(self, feed: Feed):
        self.feed = feed
        self.closed_klines = {
            "1m": 0,
            "5m": 0,
            "15m": 0,
            "1h": 0,
            "4h": 0,
            "1d": 0
        }

    def solve(self, symbol: str, timestamp: int) -> int:
        res = -1
        print(f"Checking for new data for {symbol} at {timestamp}")
        if self.closed_klines["1m"] == 0:
            print("First time running, initializing closed klines")
            for interval in self.closed_klines.keys():
                interval_ms = to_ms_interval(interval)
                self.closed_klines[interval] = timestamp // interval_ms
            return res
        res += 1
        for interval, ref in self.closed_klines.items():
            interval_ms = to_ms_interval(interval)
            ref_ = timestamp // interval_ms
            print(f"Checking for {interval} interval, ref: {ref}, ref_: {ref_}, timestamp: {timestamp}, interval_ms: {interval_ms}")
            if ref_ > ref:
                print(f"New data available for {interval} interval")
                n_data = 30
                df = self.feed.get_klines(symbol, interval, timestamp - n_data * interval_ms + 1, timestamp + 1) 
                self.closed_klines[interval] = ref_
                Pattern.recognize("liquidity", df)
                res += 1
        return res

