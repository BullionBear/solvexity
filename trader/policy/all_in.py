from decimal import Decimal
from typing import Type
from trader.core import Policy, TradeContext
from trader.data import Trade
from service.notification import Color
import pandas as pd
import helper
import helper.logging as logging

logger = logging.getLogger("trading")

class AllIn(Policy):
    """
        A policy that buys all available balance of the quote asset.
    """
    MAX_TRADE_SIZE = 65535
    MIN_QUOTE_SIZE = Decimal('10')
    def __init__(self, trade_context: Type[TradeContext], symbol: str, trade_id: str):
        super().__init__(trade_context, trade_id)
        self.symbol: str = symbol

    @property
    def base(self):
        return self.symbol[:-4] # e.g. BTCUSDT -> BTC
    
    @property
    def quote(self):
        return self.symbol[-4:] # e.g. BTCUSDT -> USDT

    def buy(self):
        quote_size = self.trade_context.get_balance(self.quote)
        ask, _ = self.trade_context.get_askbid(self.symbol)
        if quote_size > self.MIN_QUOTE_SIZE:
            size, price = helper.symbol_filter(self.symbol, quote_size / ask, ask)
            self.notify("OnMarketBuy", f"**Trade ID**: {self.id}\n**Symbol**: {self.symbol}\n **size**: {size}\n **ref price**: {price}", Color.BLUE)
            self.trade_context.market_buy(self.symbol, quote_size / ask)

    def sell(self):
        base_size = self.trade_context.get_balance(self.base)
        _, bid = self.trade_context.get_askbid(self.symbol)
        
        if base_size * bid > self.MIN_QUOTE_SIZE:
            size, price = helper.symbol_filter(self.symbol, base_size, bid)
            self.notify("OnMarketSell", f"**Trade ID**: {self.id}\n**Symbol**: {self.symbol}\n **size**: {size}\n**ref price**: {price}", Color.BLUE)
            self.trade_context.market_sell(self.symbol, base_size)

    def export(self, output_dir: str):
        trades = self.trade_context.get_trades(self.symbol, self.MAX_TRADE_SIZE)
        df = pd.DataFrame([trade.to_dict() for trade in trades])
        logger.info(f"Exporting policy {self.symbol} trades to {output_dir}")
        target_dest = f"{output_dir}/policy_{self.symbol}_{self.id}.csv"
        df.to_csv(target_dest, index=False)
        

    def notify(self, title: str, content: str, color: Color):
        super().notify(title, content, color)

    