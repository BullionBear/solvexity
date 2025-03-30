from typing import Any
import pandas as pd
import numpy as np
from solvexity.analytic.feed import Feed
import matplotlib
matplotlib.use('Agg')

class Pattern:
    def __init__(self, feed: Feed):
        self.feed: Feed = feed

    def calc_returns(self, symbol: str, interval: str, start: int, end: int) -> float:
        df = self.feed.get_klines(symbol, interval, start, end)
        return df["close_px"].iat[-1] / df["close_px"].iat[0] - 1 # Simple return calculation
    
    def calc_volatility(self, symbol: str, interval: str, start: int, end: int) -> float:
        df = self.feed.get_klines(symbol, interval, start, end)
        df["log_return"] = np.log(df["close_px"] / df["open_px"].shift(1))
        return df["log_return"].std()
    
    def calc_mdd(self, symbol: str, interval: str, start: int, end: int) -> float:
        df = self.feed.get_klines(symbol, interval, start, end)
        df["cum_return"] = (df["close_px"] / df["close_px"].iat[0]) - 1
        df["peak"] = df["cum_return"].cummax()
        df["drawdown"] = df["peak"] - df["cum_return"]
        return df["drawdown"].max()
    
    def calc_skewness(self, symbol: str, interval: str, start: int, end: int) -> float:
        df = self.feed.get_klines(symbol, interval, start, end)
        df["log_return"] = np.log(df["close_px"] / df["open_px"])
        return df["log_return"].skew()
    
    def calc_kurtosis(self, symbol: str, interval: str, start: int, end: int) -> float:
        df = self.feed.get_klines(symbol, interval, start, end)
        df["log_return"] = np.log(df["close_px"] / df["open_px"])
        return df["log_return"].kurtosis()        
        
    def calc_egarch(self, symbol: str, interval: str, start: int, end: int) -> float:
        df = self.feed.get_klines(symbol, interval, start, end)
        # Fit an EGARCH(1,1) model
        from arch import arch_model
        df["log_return"] = np.log(df["close_px"] / df["open_px"])
        model = arch_model(df["log_return"], vol="EGarch", p=1, q=1, mean="Constant", dist="Normal", rescale=True)
        fit = model.fit(disp="off")

        # Extract model parameters and fitness metrics
        results = {
            "mu": fit.params["mu"],  # Mean return
            "omega": fit.params["omega"],  # Constant term in volatility equation
            "alpha[1]": fit.params["alpha[1]"],  # ARCH term (impact of shocks)
            "beta[1]": fit.params["beta[1]"],  # GARCH term (volatility persistence)
            # "gamma[1]": fit.params["gamma[1]"],  # Asymmetry term (captures leverage effect)
            "log_likelihood": fit.loglikelihood,  # Log-likelihood of the model
            "aic": fit.aic,  # Akaike Information Criterion
            "bic": fit.bic,  # Bayesian Information Criterion
        }
        return results
    
    def stopping_return(self, symbol: str, interval: str, start: int, end: int, stop_loss: float, stop_profit: float) -> float:
        """
        Calculate the stopping return for a given symbol and interval.
        The stopping return is the average return of the asset over the specified period,
        adjusted for stop-loss and stop-profit thresholds.
        :param symbol: The trading symbol (e.g., "BTCUSDT").
        :param interval: The time interval for the data (e.g., "1m", "5m", "1h").
        :param start: The start time in milliseconds since epoch.
        :param end: The end time in milliseconds since epoch.
        :param stop_loss: The stop-loss threshold (e.g., -0.05 for 5% loss).
        :param stop_profit: The stop-profit threshold (e.g., 0.05 for 5% profit).
        :return: The stopping return over the specified period.
        """
        assert stop_loss < 0, "stop_loss must be negative"
        assert stop_profit > 0, "stop_profit must be positive"
        # Fetch data
        df = self.feed.get_klines(symbol, interval, start, end)

        # Calculate returns and stop conditions
        df["return"] = df["close_px"] / df["close_px"].iat[0] - 1
        df["stop_triggered"] = (df["return"] < stop_loss) | (df["return"] > stop_profit)

        # Find the first triggered stop condition
        first_trigger_index = df[df["stop_triggered"]].index.min()

        # Determine the stopping price
        stopping_px = df.loc[first_trigger_index, "close_px"] if not pd.isna(first_trigger_index) else df["close_px"].iat[-1]

        # Calculate and return the stopping return
        return (stopping_px / df["close_px"].iat[0]) - 1
        
        
    

    
