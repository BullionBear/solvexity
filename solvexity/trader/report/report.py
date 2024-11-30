"""
Author:     Yi Te
Created:    2024/11/24
Comment:
    I am not sure if the report should use factoty pattern or not.
    If the report instance makes good for general use, then it's OK to not use factory pattern.
"""
from enum import Enum
from typing import Type
from solvexity.trader.core import TradeContext
from solvexity.trader.data import KLine
import solvexity.helper.logging as logging
import pandas as pd
import json

logger = logging.getLogger("trading")

class INDEX(str, Enum):
    MARKET = "MARKET"
    POSITION = "POSITION"

class Report:
    def __init__(self, context: Type[TradeContext], symbol: str, limit: int):
        self.context = context
        self.symbol = symbol
        self.limit = limit

        self.position: list[KLine] = []
        self.market: list[KLine] = []

    @property
    def base(self):
        return self.symbol[:-4] # e.g. BTCUSDT -> BTC
    
    @property
    def quote(self):
        return self.symbol[-4:] # e.g. BTCUSDT -> USDT


    def _update_position(self, kline: KLine):
        """Update the position with the adjusted kline data."""
        kline = kline.model_copy()
        base_size = float(self.context.get_balance(self.base))
        quote_size = float(self.context.get_balance(self.quote))
        kline.open = base_size * kline.open + quote_size
        kline.close = base_size * kline.close + quote_size
        kline.high = base_size * kline.high + quote_size
        kline.low = base_size * kline.low + quote_size
        return kline

    def invoke(self):
        klines = self.context.get_klines(self.symbol, 1)
        if not klines:
            logger.warning(f"No kline data for {self.symbol}")
            return

        latest_kline = klines[0].model_copy()

        if not self.market:
            self.market.append(latest_kline)

        if not self.position:
            self.position.append(self._update_position(latest_kline))
        elif latest_kline.is_closed:
            self.market.append(latest_kline.model_copy())
            logger.info(f"Market Kline: {self.market[-1]}")
            self.position.append(self._update_position(latest_kline))
            logger.info(f"Position KLine: {self.position[-1]}")
            if len(self.market) > self.limit:
                self.market.pop(0)
                self.position.pop(0)
        else:
            self.market[-1] = latest_kline
            self.position[-1] = self._update_position(latest_kline)

    def export(self, output_dir: str):
        start = self.market[0].open_time
        end = self.market[-1].close_time
        report = {
            "symbol": self.symbol,
            "market": {
                "return": self.calculate_return(INDEX.MARKET),
                "volatility": self.calculate_volatility(INDEX.MARKET),
                "drawdown": self.calculate_max_drawdown(INDEX.MARKET)
            },
            "position": {
                "return": self.calculate_return(INDEX.POSITION),
                "volatility": self.calculate_volatility(INDEX.POSITION),
                "drawdown": self.calculate_max_drawdown(INDEX.POSITION)
            },
            "period": {
                "start": start,
                "end": end
            }
        }
        target_dest = f"{output_dir}/report_{self.symbol}_{start}_{end}.json"
        with open(target_dest, "w") as f:
            json.dump(report, f, indent=4)

    from enum import Enum
from typing import Type
from solvexity.trader.core import TradeContext
from solvexity.trader.data import KLine
import solvexity.helper.logging as logging
import pandas as pd
import json

logger = logging.getLogger("trading")

class INDEX(str, Enum):
    MARKET = "MARKET"
    POSITION = "POSITION"

class Report:
    def __init__(self, context: Type[TradeContext], symbol: str, limit: int):
        self.context = context
        self.symbol = symbol
        self.limit = limit

        self.position: list[KLine] = []
        self.market: list[KLine] = []

    @property
    def base(self):
        return self.symbol[:-4]  # e.g., BTCUSDT -> BTC
    
    @property
    def quote(self):
        return self.symbol[-4:]  # e.g., BTCUSDT -> USDT

    def _update_position(self, kline: KLine):
        """Update the position with the adjusted kline data."""
        kline = kline.model_copy()
        base_size = float(self.context.get_balance(self.base))
        quote_size = float(self.context.get_balance(self.quote))
        kline.open = base_size * kline.open + quote_size
        kline.close = base_size * kline.close + quote_size
        kline.high = base_size * kline.high + quote_size
        kline.low = base_size * kline.low + quote_size
        return kline

    def invoke(self):
        klines = self.context.get_klines(self.symbol, 1)
        if not klines:
            logger.warning(f"No kline data for {self.symbol}")
            return
        latest_kline = klines[0].model_copy()
        if not self.market:
            self.market.append(latest_kline)
            self.position.append(self._update_position(latest_kline))
        elif latest_kline.is_closed:
            self.market.append(latest_kline.model_copy())
            self.position.append(self._update_position(latest_kline))
            if len(self.market) > self.limit:
                self.market.pop(0)
                self.position.pop(0)
        else:
            self.market[-1] = latest_kline
            self.position[-1] = self._update_position(latest_kline)

    def export(self, output_dir: str):
        start = self.market[0].open_time
        end = self.market[-1].close_time
        report = {
            "symbol": self.symbol,
            "market": {
                "return": self.calculate_return(self.market),
                "volatility": self.calculate_volatility(self.market),
                "drawdown": self.calculate_max_drawdown(self.market)
            },
            "position": {
                "return": self.calculate_return(self.position),
                "volatility": self.calculate_volatility(self.position),
                "drawdown": self.calculate_max_drawdown(self.position)
            },
            "period": {
                "start": start,
                "end": end
            }
        }
        target_dest = f"{output_dir}/report_{self.symbol}_{start}_{end}.json"
        with open(target_dest, "w") as f:
            json.dump(report, f, indent=4)
        df = Report.to_dataframe(self.market)
        df.to_csv(f"{output_dir}/market_{self.symbol}_{start}_{end}.csv", index=False)

    @staticmethod
    def calculate_return(data: list[KLine]) -> float:
        """
        Calculate the total return.

        Args:
            data (list[KLine]): The list of KLine data.

        Returns:
            float: The percentage return based on the initial and current portfolio value.
        """
        df = Report.to_dataframe(data)
        if df.empty:
            return 0.0
        initial_value = df.iloc[0]["close"]
        final_value = df.iloc[-1]["close"]
        return ((final_value - initial_value) / initial_value) * 100

    @staticmethod
    def calculate_volatility(data: list[KLine]) -> float:
        """
        Calculate the volatility.

        Args:
            data (list[KLine]): The list of KLine data.

        Returns:
            float: The standard deviation of returns as a measure of volatility.
        """
        df = Report.to_dataframe(data)
        if df.empty:
            return 0.0
        df["returns"] = df["close"].pct_change()
        return df["returns"].std()

    @staticmethod
    def calculate_max_drawdown(data: list[KLine]) -> dict:
        """
        Calculate the maximum drawdown with additional details.

        Args:
            data (list[KLine]): The list of KLine data.

        Returns:
            dict: A dictionary containing:
                - "percentage": The maximum drawdown as a percentage of the peak portfolio value.
                - "start": The timestamp when the drawdown started.
                - "from": The timestamp of the lowest point during the drawdown.
        """
        df = Report.to_dataframe(data)
        if df.empty:
            return {"percentage": 0.0, "start": None, "from": None}

        # Convert open_time to a readable datetime format
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')

        # Calculate the cumulative max using the high prices and drawdown using the low prices
        df['cumulative_high'] = df['high'].cummax()
        df['drawdown'] = (df['low'] - df['cumulative_high']) / df['cumulative_high']

        # Find the maximum drawdown
        max_drawdown = df['drawdown'].min()
        max_drawdown_row = df[df['drawdown'] == max_drawdown]

        # Identify the start of the drawdown (max cumulative high before the drawdown)
        drawdown_start_index = df.loc[:max_drawdown_row.index[0]]['high'].idxmax()
        drawdown_start_time = df.loc[drawdown_start_index, 'open_time']

        # Identify the end of the drawdown (minimum low during the drawdown period)
        drawdown_end_time = max_drawdown_row['open_time'].iloc[0]

        max_drawdown, drawdown_start_time, drawdown_end_time
        return {
            "percentage": max_drawdown,
            "start": int(drawdown_start_time.timestamp() * 1000),
            "from": int(drawdown_end_time.timestamp() * 1000)
        }

    @staticmethod
    def to_dataframe(data: list[KLine]) -> pd.DataFrame:
        """
        Convert a list of KLine objects to a Pandas DataFrame.

        Args:
            data (list[KLine]): The list of KLine objects.

        Returns:
            pd.DataFrame: The DataFrame representation of the KLine data.
        """
        data_dict = [kline.model_dump() for kline in data]
        return pd.DataFrame(data_dict)