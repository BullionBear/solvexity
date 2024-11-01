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

    @property
    def base(self):
        return self.symbol[-3:]
    
    @property
    def quote(self):
        return self.quote[:-3]
    
    def get_balance(self):
        logger.info(f"{self.base} balance = {self.client.get_asset_balance(asset=self.base)}")
        # self.client.get_asset_balance(asset=self.quote)

    def invoke(self, data: list[KLine]):
        pass

    def is_buy(self):
        return True
    
    
    def is_sell(self):
        return False
    
    @staticmethod
    def to_dataframe(data: list[KLine]):
        pass