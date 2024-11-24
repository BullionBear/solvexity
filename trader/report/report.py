"""
Author:     Yi Te
Created:    2024/11/24
Comment:
    I am not sure if the report should use factoty pattern or not.
    If the report instance makes good for general use, then it's OK to not use factory pattern.
"""
from enum import Enum
from typing import Type
from trader.core import TradeContext
from trader.data import KLine
import helper.logging as logging

logger = logging.getLogger("trading")

class INDEX(str, Enum):
    MARKET = "MARKET"
    POSITION = "POSITION"

class Report:
    def __init__(self, context: Type[TradeContext], symbol: str, limit: int):
        self.context = context
        self.symbol = symbol

        self.balance = self.context.get_balance(self.symbol)
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
        base_size = self.balance[self.base]
        quote_size = self.balance[self.quote]
        kline.open = base_size * kline.open + quote_size
        kline.close = base_size * kline.close + quote_size
        kline.high = base_size * kline.high + quote_size
        kline.low = base_size * kline.low + quote_size
        return kline.model_copy()

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
        elif latest_kline.is_close:
            self.market.append(latest_kline)
            self.position.append(self._update_position(latest_kline))
            if len(self.market) > self.limit:
                self.market.pop(0)
                self.position.pop(0)
        else:
            self.market[-1] = latest_kline
            self.position[-1] = self._update_position(latest_kline)


    def calculate_return(self, flag: INDEX) -> float:
        """
        Calculate the total return of the trading strategy.

        Returns:
            float: The percentage return based on the initial and current portfolio value.
        """
        pass

    def calculate_volatility(self, flag: INDEX) -> float:
        """
        Calculate the volatility of the portfolio.

        Returns:
            float: The standard deviation of returns as a measure of volatility.
        """
        pass

    def calculate_max_drawdown(self, flag: INDEX) -> float:
        """
        Calculate the maximum drawdown of the portfolio.

        Returns:
            float: The maximum drawdown as a percentage of the peak portfolio value.
        """
        pass
