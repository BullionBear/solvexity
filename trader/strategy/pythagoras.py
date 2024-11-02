import time
import pandas as pd
from decimal import Decimal, ROUND_DOWN
import binance.client as BinanceClient
import helper.logging as logging
import helper
from .notification import (
    on_trading_start, on_trading_finish, on_order_sent, on_error
)
from trader.data import KLine

logger = logging.getLogger("trading")

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
            logger.error(f"Data is not updated: {data[-1].to_dict()}")
            helper.send_notification(self.webhook_url, None, self.family, 
                                     on_error(self.family, id=self._id, error="Data is not updated")
                                     )
            return
        df = self.to_dataframe(data)
        df_analysis = self.analyze(df)
        if self.is_buy(df_analysis):
            kline = data[-1]
            ask, _ = self.get_askbid()
            sz = Decimal(self.balance[self.base]) / Decimal(ask)
            self.market_buy(str(sz))
        elif self.is_sell():
            self.market_sell(self.balance[self.base])

    def analyze(self, df: pd.DataFrame):
        df_analysis = df.copy()
        df_analysis['fast_ma'] = df_analysis['close'].rolling(window=self.trading_meta["fast_ma_period"]).mean()
        df_analysis['slow_ma'] = df_analysis['close'].rolling(window=self.trading_meta["slow_ma_period"]).mean()
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
            return False
        if last_update['fast_ma'].values[0] > last_update['slow_ma'].values[0]:
            return False
        if last_update['close'].values[0] > last_update['fast_ma'].values[0]:
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
        if self.balance[self.quote] * px > self.balance[self.base]:
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
            self.client.order_market_buy(symbol=self.symbol, quantity=str(qty))
        except Exception as e:
            logger.error(f"Failed to place market buy order: {e}")
            helper.send_notification(self.webhook_url, None, self.family, 
                                     on_error(self.family, id=self._id, error=e)
                                     )
    
    @staticmethod
    def to_dataframe(data: list[KLine]):
        data_dict = [kline.model_dump() for kline in data]
        return pd.DataFrame(data_dict)