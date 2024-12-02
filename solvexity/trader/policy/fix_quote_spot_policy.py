from decimal import Decimal
from typing import Type
from solvexity.trader.core import Policy, TradeContext
from solvexity.trader.model import Trade
from solvexity.dependency.notification import Color
import pandas as pd
import solvexity.helper as helper
import solvexity.helper.logging as logging

logger = logging.getLogger("trading")

class FixQuoteSpotPolicy(Policy):
    """
        A policy that buys all available balance of the quote asset.
    """
    def __init__(self, trade_context: Type[TradeContext], symbol: str, quote_size: float, trade_id: str):
        super().__init__(trade_context, trade_id)
        self.symbol: str = symbol
        self.quote_size = Decimal(quote_size)

    @property
    def base(self):
        return self.symbol[:-4] # e.g. BTCUSDT -> BTC
    
    @property
    def quote(self):
        return self.symbol[-4:] # e.g. BTCUSDT -> USDT
    
    def buy(self):
        total_quote_size = self.trade_context.get_avaliable_balance(self.quote)
        ask, _ = self.trade_context.get_askbid(self.symbol)
        if total_quote_size > self.quote_size:
            size, price = helper.symbol_filter(self.symbol, self.quote_size / ask, ask)
            self.notify("OnMarketBuy", f"**Trade ID**: {self.id}\n**Symbol**: {self.symbol}\n**size**: {size}\n **ref price**: {price}", Color.BLUE)
            self.trade_context.market_buy(self.symbol, self.quote_size / ask)

    def sell(self):
        total_base_size = self.trade_context.get_avaliable_balance(self.base)
        _, bid = self.trade_context.get_askbid(self.symbol)
        
        if total_base_size * bid > self.quote_size:
            base_size = self.quote_size / bid
            size, price = helper.symbol_filter(self.symbol, base_size, bid)
            self.notify("OnMarketSell", f"**Trade ID**: {self.id}\n**Symbol**: {self.symbol}\n**size**: {size}\n**ref price**: {price}", Color.BLUE)
            self.trade_context.market_sell(self.symbol, base_size)
        else:
            logger.error(f"Insufficient base size {total_base_size} for {self.symbol}")

    def export(self, output_dir: str):
        trades = self.trade_context.get_trades(self.symbol, self.MAX_TRADE_SIZE)
        df = pd.DataFrame([trade.dict() for trade in trades])
        logger.info(f"Exporting policy {self.symbol} trades to {output_dir}")
        target_dest = f"{output_dir}/policy_{self.symbol}_{self.id}.csv"
        df.to_csv(target_dest, index=False)
        

    def notify(self, title: str, content: str, color: Color):
        super().notify(title, content, color)