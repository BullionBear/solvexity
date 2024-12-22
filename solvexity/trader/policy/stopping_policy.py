from decimal import Decimal
from typing import Type
import solvexity.helper as helper
from solvexity.trader.core import Policy, TradeContext
from solvexity.trader.model import Order
from solvexity.trader.core import SignalType
from solvexity.dependency.notification import Color
import pandas as pd
import solvexity.helper as helper
import solvexity.helper.logging as logging

logger = logging.getLogger()

class StoppingPolicy(Policy):
    """
        A policy that buy/sell fix quote size of the quote asset. Always set a stoploss market order
        For example, if price of BTCUSDT is 50000, quote_size is 1000, stoploss_quote is 100, then 
        the policy will buy 0.02 BTC at 50000, and set a stoploss market order at 49000
    """
    def __init__(self, 
                 trade_context: Type[TradeContext], 
                 symbol: str, 
                 quote_size: float, 
                 profit_quote: float, 
                 loss_quote: float, 
                 lifecycle: int,
                 trade_id: str):
        super().__init__(trade_context, trade_id)
        self.symbol: str = symbol
        self.quote_size = Decimal(quote_size)
        self.stop_loss_pct = Decimal(profit_quote / quote_size)
        self.stop_profit_pct = Decimal(loss_quote / quote_size)
        self.lifecycle = lifecycle
        if 0 <= self.lifecycle <= helper.to_unixtime_interval('1m'):
            raise ValueError("Lifecycle should be greater than 1 minute")
        self._pending_orders = []

    @property
    def base(self):
        return self.symbol[:-4] # e.g. BTCUSDT -> BTC
    
    @property
    def quote(self):
        return self.symbol[-4:] # e.g. BTCUSDT -> USDT
    
    def act(self, signal: SignalType):
        ask, bid = self.trade_context.get_askbid(self.symbol)
        self.trigger_trailing_stop(ask, bid)
        if signal == SignalType.BUY:
            self.buy(ask)
        elif signal == SignalType.SELL:
            self.sell(bid)
        elif signal == SignalType.HOLD:
            pass
        else:
            logger.error(f"Unknown signal type {signal}", exc_info=True)
    
    def buy(self, px):
        try:
            size, px = helper.symbol_filter(self.symbol, self.quote_size / px, px)
            logger.info(f"Long {size} {self.symbol} at {px}")
            self.notify("OnMarketLong", f"**Trade ID**: {self.id}\n**Symbol**: {self.symbol}\n**size**: {size}\n**ref price**: {px}", Color.MAGENTA)
            res = self.trade_context.market_buy(self.symbol, size)
            logger.info(f"Order response: {res}")
            stop_px = px * (Decimal('1') - self.slippage)
            size, stop_px = helper.symbol_filter(self.symbol, size, stop_px)
            trailing_order = {
                "size": size,
                "px": stop_px
            }
            self._stoploss_sell_order.append(trailing_order)
        except Exception as e:
            logger.error(f"Market long failed: {e}", exc_info=True)

    def sell(self, px):
        try:
            size, px = helper.symbol_filter(self.symbol, self.quote_size / px, px)
            logger.info(f"Short {size} {self.symbol} at {px}")
            self.notify("OnMarketShort", f"**Trade ID**: {self.id}\n**Symbol**: {self.symbol}\n**size**: {size}\n**ref price**: {px}", Color.MAGENTA)
            res = self.trade_context.market_sell(self.symbol, size)
            logger.info(f"Order response: {res}")
            stop_px = px * (Decimal('1') + self.slippage)
            size, stop_px = helper.symbol_filter(self.symbol, size, stop_px)
            trailing_order = {
                "size": size,
                "px": stop_px
            }
            self._stoploss_buy_order.append(trailing_order)
        except Exception as e:
            logger.error(f"Market short failed: {e}", exc_info=True)

    def close(self):
        super().close()
    

    
    