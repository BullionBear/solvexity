from typing import Any
import pandas as pd
import numpy as np
import pwlf

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