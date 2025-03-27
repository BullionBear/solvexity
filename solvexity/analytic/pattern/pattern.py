from typing import Any
import pandas as pd
import numpy as np
import pwlf

import matplotlib
matplotlib.use('Agg')

class Pattern:

    @staticmethod
    def recognize(method: str, df: pd.DataFrame) -> dict[str, Any]:
        return {method: Pattern._recognize(method, df)}

    @staticmethod
    def _recognize(method: str, df: pd.DataFrame) -> dict[str, float]:
        if method == "liquidity":
            return Pattern._calc_liquidity(df)
        else:
            raise ValueError(f"Method {method} not supported")
        
    @staticmethod
    def _calc_liquidity(df: pd.DataFrame) -> float:
        import mplfinance as mpf
        
        df = df.copy()
        df['support_time'] = np.nan

        # Calculate support_time
        for i in range(len(df)):
            low = df.loc[i, 'low_px']
            for j in range(i - 1, -1, -1):
                if df.loc[j, 'low_px'] < low < df.loc[j, 'high_px']:
                    df.loc[i, 'support_time'] = df.loc[j, 'open_time']
                    break
        df['support'] = df.apply(
            lambda row: df[df['open_time'] == row['support_time']]['low_px'].values[0]
            if not np.isnan(row['support_time']) else row['low_px'],
            axis=1
        )
        df['support_time_diff'] = df['open_time'] - df['support_time']
        n_support_segment = df['support_time_diff'].sum() / (df['open_time'].iat[-1] - df['open_time'].iat[0]) + 1

        df['resistance_time'] = np.nan

        # Calculate resistance_time
        for i in range(len(df)):
            high = df.loc[i, 'high_px']
            for j in range(i - 1, -1, -1):
                if df.loc[j, 'low_px'] < high < df.loc[j, 'high_px']:
                    df.loc[i, 'resistance_time'] = df.loc[j, 'open_time']
                    break
                
        df['resistance'] = df.apply(
            lambda row: df[df['open_time'] == row['resistance_time']]['high_px'].values[0]
            if not np.isnan(row['resistance_time']) else row['high_px'],
            axis=1
        )
        df['resistance_time_diff'] = df['open_time'] - df['resistance_time']

        n_resistance_segment = df['resistance_time_diff'].sum() / (df['open_time'].iat[-1] - df['open_time'].iat[0]) + 1
        x_hat = df['open_time']

        model_support = pwlf.PiecewiseLinFit(df['open_time'], df['support'])
        _ = model_support.fit(n_support_segment)
        df['support_pred'] = model_support.predict(x_hat)
        df['support_pred_variance'] = model_support.prediction_variance(x_hat)
        df['support_pred_lower'] = df['support_pred'] - 2 * np.sqrt(df['support_pred_variance'])
        model_resistance = pwlf.PiecewiseLinFit(df['open_time'], df['resistance'])
        _ = model_resistance.fit(n_resistance_segment)
        x_hat = df['open_time']
        df['resistance_pred'] = model_resistance.predict(x_hat)
        df['resistance_pred_variance'] = model_resistance.prediction_variance(x_hat)
        df['resistance_pred_upper'] = df['resistance_pred'] + 2 * np.sqrt(df['resistance_pred_variance'])

        df_plot = df.copy()

        df_plot['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df_plot.set_index('open_time', inplace=True)
        # Rename columns to match mplfinance expectations
        df_plot.rename(columns={
            'open_px': 'Open',
            'high_px': 'High',
            'low_px': 'Low',
            'close_px': 'Close',
            'base_asset_volume': 'Volume'
        }, inplace=True)
        # Select only the required columns for plotting
        df_plot = df_plot[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
        df_plot = df_plot[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
        apds = [mpf.make_addplot(df['support_pred'], type='line', color='green', linestyle='dashed'),
                mpf.make_addplot(df['resistance_pred'], type='line', color='red', linestyle='dashed')]
        apds.extend([
            mpf.make_addplot(df['support_pred_lower'], type='line', color='green', linestyle='dotted'),
            mpf.make_addplot(df['resistance_pred_upper'], type='line', color='red', linestyle='dotted')
        ])
        timestamp = df['open_time'].iat[-1]
        symbol = df['symbol'].iat[0]
        interval = df['interval'].iat[0]
        # Format filename
        date_str = pd.to_datetime(timestamp, unit='ms').strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"./verbose/{symbol}_{interval}_liquidity_{date_str}.png"
        # Plot and save the candlestick chart
        mpf.plot(
            df_plot,
            type='candle',
            style='charles',
            volume=True,
            title=f"{symbol} Candlestick - {date_str}",
            addplot=apds,
            savefig=dict(fname=filename, dpi=150)
        )
        return 0