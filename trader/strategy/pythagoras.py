import sys
import pandas as pd
import binance.client as BinanceClient
import helper.logging as logging
from trader.data import KLine

logger = logging.getLogger("trading")

class Pythagoras:
    def __init__(self, binance_client: BinanceClient, trading_config: dict):
        self.client = binance_client
        self.symbol = trading_config["symbol"]
        self.balance = {
            self.base: 0,
            self.quote: 0
        }
        self.get_balance()

    @property
    def base(self):
        return self.symbol[-4:]
    
    @property
    def quote(self):
        return self.symbol[:-4]
    
    def get_balance(self):
        self.balance[self.base] = float(self.client.get_asset_balance(asset=self.base)['free'])
        self.balance[self.quote] = float(self.client.get_asset_balance(asset=self.quote)['free'])
        logger.info(f"Current balance: {self.balance}")

    def invoke(self, data: list[KLine]):
        df = self.to_dataframe(data)
        df.to_csv("data.csv", index=False)
        sys.exit(0)
        

    def is_buy(self):
        return True
    
    
    def is_sell(self):
        return False
    
    @staticmethod
    def to_dataframe(data: list[KLine]):
        data_dict = [kline.model_dump() for kline in data]
        return pd.DataFrame(data_dict)