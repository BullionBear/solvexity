import sys
import pandas as pd
import binance.client as BinanceClient
import helper.logging as logging
import helper
from .notification import on_trading_start
from trader.data import KLine

logger = logging.getLogger("trading")

class Pythagoras:
    def __init__(self, binance_client: BinanceClient, trading_config: dict, webhook_url: str):
        self.client = binance_client
        self._id = helper.generate_random_id()
        self.symbol = trading_config["symbol"]
        self.balance = self.get_balance()
        self.webhook_url = webhook_url
        self.trading_metadata = trading_config["meta"]
    
    def __enter__(self):
        helper.send_notification(self.webhook_url, None, "Pythagoras", on_trading_start("Pythagoras", symbol=self.symbol, id=self._id, **self.trading_metadata))
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        helper.send_notification(self.webhook_url, None, "Pythagoras", on_trading_start("Pythagoras", symbol=self.symbol, id=self._id))
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
    
    def get_askbid(self):
        return self.client.get_order_book(symbol=self.symbol, limit=1)
    
    
    def get_balance(self):
        balance = {
            self.base: float(self.client.get_asset_balance(asset=self.base)['free']),
            self.quote: float(self.client.get_asset_balance(asset=self.quote)['free'])
        }
        logger.info(f"Current balance: {balance}")
        return balance

    def invoke(self, data: list[KLine]):
        df = self.to_dataframe(data)
        return
        

    def is_buy(self):
        return True
    
    def buy(self, price: float, quantity: float):
        pass
    
    def sell(self, price: float, quantity: float):
        pass
    
    def is_sell(self):
        return False
    
    def stop(self):
        pass
    
    @staticmethod
    def to_dataframe(data: list[KLine]):
        data_dict = [kline.model_dump() for kline in data]
        return pd.DataFrame(data_dict)