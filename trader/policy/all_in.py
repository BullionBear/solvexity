from decimal import Decimal
from typing import Type
from trader.core import Policy, TradeContext
import helper.logging as logging

logger = logging.getLogger("trading")

class AllIn(Policy):
    """
        A policy that buys all available balance of the quote asset.
    """
    MIN_QUOTE_SIZE = Decimal('10')
    def __init__(self, trade_context: Type[TradeContext], symbol: str):
        super().__init__(trade_context)
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
            self.trade_context.market_buy(self.symbol, quote_size / ask)

    def sell(self):
        base_size = self.trade_context.get_balance(self.base)
        _, bid = self.trade_context.get_askbid(self.symbol)
        
        if base_size * bid > self.MIN_QUOTE_SIZE:
            self.trade_context.market_sell(self.symbol, base_size)

    