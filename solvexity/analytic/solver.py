import pandas as pd
import matplotlib
matplotlib.use('Agg')
import mplfinance as mpf

from .feed import Feed
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
            if ref_ > ref:
                print(f"New data available for {interval} interval")
                n_data = 30
                df = self.feed.get_klines(symbol, interval, timestamp - n_data * interval_ms + 1, timestamp + 1) 
                self.closed_klines[interval] = ref_
                self.plot_kline(df, symbol, interval, timestamp)
                res += 1
            return res

    def plot_kline(self, df: pd.DataFrame, symbol: str, interval: str, timestamp: int):
        if df.empty:
            print("No data to plot.")
            return
        # Rename and convert timestamp to datetime index
        df = df.copy()
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df.set_index('open_time', inplace=True)
        # Rename columns to match mplfinance expectations
        df.rename(columns={
            'open_px': 'Open',
            'high_px': 'High',
            'low_px': 'Low',
            'close_px': 'Close',
            'base_asset_volume': 'Volume'
        }, inplace=True)

        # Select only the required columns for plotting
        df_plot = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)

        # Format filename
        date_str = pd.to_datetime(timestamp, unit='ms').strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"./verbose/{symbol}_{interval}_{date_str}.png"
        df.to_csv(filename.replace('.png', '.csv'), index=False)

        # Plot and save the candlestick chart
        mpf.plot(
            df_plot,
            type='candle',
            style='charles',
            volume=True,
            title=f"{symbol} Candlestick - {date_str}",
            savefig=dict(fname=filename, dpi=150)
        )

        print(f"Saved candlestick chart to {filename}")
