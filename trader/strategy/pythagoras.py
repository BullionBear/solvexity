import time
import pandas as pd
from decimal import Decimal, ROUND_DOWN
from trader.core import TradeContext, Strategy
import helper.logging as logging
from .notification import (
    on_trading_start, on_trading_finish, on_order_sent, on_error
)
from trader.data import KLine

logger = logging.getLogger("trading")

class Pythagoras(Strategy):
    def __init__(self, trade_context: TradeContext, symbol: str, limit: int, metadata: dict, trade_id = None):
        super().__init__(trade_context, trade_id)
        self.family = "Pythagoras"
        self.symbol = symbol
        self.limit = limit
        self.metadata = metadata
        logger.info(f"Init balance:  {self.base}: {self.get_balance(self.base)}, {self.quote}: {self.get_balance(self.quote)}")
    
    def __enter__(self):
        self.trade_context.notify(**on_trading_start(self.family, id=self._id, symbol=self.symbol, **self.metadata))
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
    # Check if an exception occurred
        if exc_type is not None:
        # Log or display the error details
            error_message = f"Error in {self.family} strategy: {exc_type.__name__} - {exc_val}"
            self.trade_context.notify(error=error_message, id=self._id, symbol=self.symbol)

            # Optionally, handle the traceback or print it
            import traceback
            traceback_str = ''.join(traceback.format_exception(exc_type, exc_val, exc_tb))
            logger.error(traceback_str)  # Or use logging instead of print

        # Notify the trading finish regardless of error
        self.trade_context.notify(**on_trading_finish(self.family, id=self._id, symbol=self.symbol))
        return False  # Propagate the exception if needed
    
    @property
    def base(self):
        return self.symbol[-4:]
    
    @property
    def quote(self):
        return self.symbol[:-4]
    
    @property
    def exchange_metadata(self):
        metadata = {}
        filters = self.client.get_symbol_info(self.symbol)['filters']
        for _filter in filters:
            if _filter['filterType'] == 'LOT_SIZE':
                metadata['lot_size'] = _filter['stepSize'].rstrip('0')
            elif _filter['filterType'] == 'PRICE_FILTER':
                metadata['lot_size'] = _filter['tickSize'].rstrip('0')
        return metadata
    
    def market_buy(self, symbol: str, size: Decimal):
        super().market_buy(symbol, size)

    def market_sell(self, symbol: str, size: Decimal):
        super().market_sell(symbol, size)

    def get_balance(self, token: str) -> Decimal:
        return super().get_balance(token)
    
    def invoke(self):
        data = super().get_klines(self.symbol, self.limit)
        if not data:
            logger.error("No data to analyze in invoke method")
            self.notify(family=self.family, **on_error(self.family, id=self._id, error="No data to analyze in invoke method"))
            return
        df = self.to_dataframe(data)
        df_analysis = self.analyze(df)
        if self.is_buy(df_analysis):
            ask, _ = self.get_askbid()
            sz = Decimal(self.balance[self.base]) / Decimal(ask)
            self.market_buy(str(sz))
        elif self.is_sell(df_analysis):
            self.market_sell(self.balance[self.base])

    def is_buy(self, df: pd.DataFrame):
        """
        Buy Logic:
            If slow_ma.diff > 0, that means the trend is going up, then we find a price is lower enough to buy.
        """
        last_update = df.tail(1)
        
        if self.is_hold(last_update['close'].values[0]):
            return False
        if last_update['slow_ma.diff'].values[0] < 0:
            logger.info(f"Trend {last_update['slow_ma.diff'].values[0]} is going down, not buying")
            return False
        if last_update['fast_ma'].values[0] > last_update['slow_ma'].values[0]:
            logger.info("Fast MA is above Slow MA, not buying")
            return False
        if last_update['close'].values[0] > last_update['fast_ma'].values[0]:
            logger.info("Price is still high, not buying")
            return False
        df_condition = df[df['fast_ma'] > df['close']]
        if df_condition.empty:
            return False
        df_condition['drawdown'] = (df_condition['fast_ma'] - df_condition['close']) / df_condition['fast_ma']
        q = df_condition['drawdown'].quantile(0.25) # q is negative
        logger.info(f"Trigger buy px should below {last_update['fast_ma'].values[0] * (1 + q)}")
        if last_update['close'].values[0] > last_update['fast_ma'].values[0] * (1 + q):
            return False
        return True
    
    def is_sell(self, df: pd.DataFrame):
        last_update = df.tail(1)
        if not self.is_hold(last_update['close'].values[0]):
            return False
        if last_update['slow_ma.diff'].values[0] < 0:
            logger.warning("Stop loss triggered")
            return True # stop loss
        if last_update['fast_ma'].values[0] < last_update['slow_ma'].values[0]:
            logger.info("Fast MA is below slow MA, not selling")
            return False
        df_condition = df[df['fast_ma'] < df['close']]
        if df_condition.empty:
            return False
        df_condition['gain'] = (df_condition['close'] - df_condition['fast_ma']) / df_condition['fast_ma']
        q = df_condition['gain'].quantile(0.25)
        logger.info(f"Trigger buy px should below {last_update['fast_ma'].values[0] * (1 + q)}")
        if last_update['close'].values[0] < last_update['fast_ma'].values[0] * (1 + q):
            return False
        return True
    
    def is_hold(self, px: float):
        if float(self.get_balance(self.quote)) * px > float(self.get_balance(self.base)):
            return True
        return False

    def analyze(self, df: pd.DataFrame):
        df_analysis = df.copy()
        df_analysis['fast_ma'] = df_analysis['close'].rolling(window=self.metadata["fast_ma_period"]).mean()
        df_analysis['slow_ma'] = df_analysis['close'].rolling(window=self.metadata["slow_ma_period"]).mean()
        df_analysis['slow_ma.diff'] = df_analysis['slow_ma'].diff()
        return df_analysis.dropna()

    def notify(self, **kwargs):
        return super().notify(**kwargs)

    @staticmethod
    def to_dataframe(data: list[KLine]):
        data_dict = [kline.model_dump() for kline in data]
        return pd.DataFrame(data_dict)
