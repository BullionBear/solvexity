from decimal import Decimal
from typing import Type
from solvexity.trader.core import Policy, TradeContext
from solvexity.trader.model import Trade
from solvexity.dependency.notification import Color
import pandas as pd
import solvexity.helper as helper
import solvexity.helper.logging as logging

logger = logging.getLogger()

class TrailingStopPerpPolicy:
    """
        A policy that buy/sell fix quote size of the quote asset. Always set a stoploss market order
        For example, if price of BTCUSDT is 50000, quote_size is 1000, stoploss_quote is 100, then 
        the policy will buy 0.02 BTC at 50000, and set a stoploss market order at 49000
    """
    def __init__(self, trade_context: Type[TradeContext], symbol: str, quote_size: float, slippage: float, trade_id: str):
        super().__init__(trade_context, trade_id)
        self.symbol: str = symbol
        self.quote_size = Decimal(quote_size)
        self.slippage = Decimal(slippage)

        self._stoploss_buy_order: list[dict] = []
        self._stoploss_sell_order: list[dict] = []

    @property
    def base(self):
        return self.symbol[:-4] # e.g. BTCUSDT -> BTC
    
    @property
    def quote(self):
        return self.symbol[-4:] # e.g. BTCUSDT -> USDT
    
    def buy(self):
        ask, _ = self.trade_context.get_askbid(self.symbol)
        
        try:
            size, price = helper.symbol_filter(self.symbol, self.quote_size / ask, ask)
            logger.info(f"Long {self.size} {self.symbol} at {price}")
            self.notify("OnMarketLong", f"**Trade ID**: {self.id}\n**Symbol**: {self.symbol}\n**size**: {sz}\n**ref price**: {ask}", Color.MAGENTA)
            res = self.trade_context.market_buy(self.symbol, self.base_size)
            logger.info(f"Order response: {res}")
        except Exception as e:
            logger.error(f"Market long failed: {e}", exc_info=True)

    def sell(self):
        logger.info(f"Selling {self.quote_size} {self.quote} for {self.symbol}")
        total_base_size = self.trade_context.get_avaliable_balance(self.base)
        _, bid = self.trade_context.get_askbid(self.symbol)
        
        if total_base_size * bid > self.quote_size:
            base_size = self.quote_size / bid
            size, price = helper.symbol_filter(self.symbol, base_size, bid)
            self.notify("OnMarketSell", f"**Trade ID**: {self.id}\n**Symbol**: {self.symbol}\n**size**: {size}\n**ref price**: {price}", Color.BLUE)
            res = self.trade_context.market_sell(self.symbol, base_size)
            logger.info(f"Order response: {res}")
        else:
            logger.error(f"Insufficient base size {total_base_size} for {self.symbol}")

    

    
    