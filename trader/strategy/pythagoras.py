import time
import pandas as pd
from decimal import Decimal, ROUND_DOWN
from trader.core import TradeContext, Strategy
import binance.client as BinanceClient
import helper.logging as logging
from .notification import (
    on_trading_start, on_trading_finish, on_order_sent, on_error
)
from trader.data import KLine

logger = logging.getLogger("trading")

class Pythagoras(Strategy):
    def __init__(self, trade_context: TradeContext, trading_config: dict, trade_id = None):
        super().__init__(trade_context, trade_id)
        self.symbol = trading_config["symbol"]
        self.limit = trading_config["limit"]
        self.trading_metadata = trading_config["metadata"]
    
    def __enter__(self):
        self.trade_context.notify(on_trading_start(self.family, id=self._id, symbol=self.symbol, **self.trading_metadata))
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.trade_context.notify(on_trading_finish(self.family, id=self._id, symbol=self.symbol))
        return self
    
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
        super().get_klines(self.symbol, self.limit)


    

    

    
        


class Pythagoras:
    def __init__(self, binance_client: BinanceClient, trading_config: dict, webhook_url: str):
        self.family = "Pythagoras"
        self.client = binance_client
        self._id = helper.generate_random_id()
        self.symbol = trading_config["symbol"]
        self.balance = self.get_balance()
        self.webhook_url = webhook_url
        self.trading_metadata = trading_config["metadata"]
    
    def __enter__(self):
        helper.send_notification(self.webhook_url, None, self.family, on_trading_start(self.family, id=self._id, symbol=self.symbol, **self.trading_metadata))
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        helper.send_notification(self.webhook_url, None, self.family, on_trading_finish(self.family, id=self._id, symbol=self.symbol))
        return self

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
    
    def get_balance(self):
        user_assets = self.client.get_user_asset(needBtcValuation=True)
        balance = {}
        for asset in user_assets:
            balance[asset['asset']] = str(Decimal(asset['free']) + Decimal(asset['locked']))
        if self.base not in balance:
            balance[self.base] = '0'
        if self.quote not in balance:
            balance[self.quote] = '0'
        logger.info(f"Current balance: {balance}")
        return balance
    
    def get_askbid(self)-> tuple[str, str]:
        order_book = self.client.get_order_book(symbol=self.symbol, limit=1)
        return order_book['asks'][0][0], order_book['bids'][0][0]

    def invoke(self, data: list[KLine]):
        if not data:
            logger.error("No data to analyze in invoke method")
            helper.send_notification(self.webhook_url, None, self.family, 
                                     on_error(self.family, id=self._id, error="No data to analyze in invoke method")
                                     )
            return
        if not self.is_updated(data[-1].event_time):
            logger.error(f"Data is not updated")
            helper.send_notification(self.webhook_url, None, self.family, 
                                     on_error(self.family, id=self._id, error="Data is not updated")
                                     )
            return
        df = self.to_dataframe(data)
        df_analysis = self.analyze(df)
        if self.is_buy(df_analysis):
            ask, _ = self.get_askbid()
            sz = Decimal(self.balance[self.base]) / Decimal(ask)
            self.market_buy(str(sz))
        elif self.is_sell(df_analysis):
            self.market_sell(self.balance[self.base])

    def analyze(self, df: pd.DataFrame):
        df_analysis = df.copy()
        df_analysis['fast_ma'] = df_analysis['close'].rolling(window=self.trading_metadata["fast_ma_period"]).mean()
        df_analysis['slow_ma'] = df_analysis['close'].rolling(window=self.trading_metadata["slow_ma_period"]).mean()
        df_analysis['slow_ma.diff'] = df_analysis['slow_ma'].diff()
        return df_analysis.dropna()
        
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
        if float(self.balance[self.quote]) * px > float(self.balance[self.base]):
            return True
        return False
    
    @staticmethod
    def is_updated(ts: int, recv_window: int = 10000):
        current_time = int(time.time() * 1000)
        return ts > current_time - recv_window
    
    def market_buy(self, quantity: float):
        qty = Decimal(quantity).quantize(Decimal(self.exchange_metadata['lot_size']), rounding=ROUND_DOWN)
        try:
            helper.send_notification(self.webhook_url, None, self.family, 
                                     on_order_sent(self.family, id=self._id, symbol=self.symbol, side="BUY", quantity=str(qty))
                                     )
            self.client.order_market_buy(symbol=self.symbol, quantity=str(qty))
        except Exception as e:
            logger.error(f"Failed to place market buy order: {e}")
            helper.send_notification(self.webhook_url, None, self.family, 
                                     on_error(self.family, id=self._id, error=e)
                                     )            
    
    def market_sell(self, quantity: float):
        qty = Decimal(quantity).quantize(Decimal(self.exchange_metadata['lot_size']), rounding=ROUND_DOWN)
        try:
            helper.send_notification(self.webhook_url, None, self.family, 
                                     on_order_sent(self.family, id=self._id, symbol=self.symbol, side="SELL", quantity=str(qty))
                                     )
            self.client.order_market_sell(symbol=self.symbol, quantity=str(qty))
        except Exception as e:
            logger.error(f"Failed to place market buy order: {e}")
            helper.send_notification(self.webhook_url, None, self.family, 
                                     on_error(self.family, id=self._id, error=e)
                                     )
    
    @staticmethod
    def to_dataframe(data: list[KLine]):
        data_dict = [kline.model_dump() for kline in data]
        return pd.DataFrame(data_dict)