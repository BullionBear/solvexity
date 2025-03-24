from .feed import Feed
import mplfinance as mpf
import matplotlib
import pandas as pd

class Solver:
    def __init__(self, feed: Feed):
        self.feed = feed

    def solve(self, symbol: str, timestamp: int):
        df_15m = self.feed.get_klines(symbol, "15m", timestamp - 86400_000, timestamp)
        self.plot_kline(df_15m, symbol, timestamp)

    def plot_kline(self, df: pd.DataFrame, symbol: str, timestamp: int):
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
        filename = f"./verbose/{symbol}_{date_str}.png"

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
