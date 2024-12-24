from decimal import Decimal
from typing import Type
import solvexity.helper as helper
from solvexity.trader.core import Policy, TradeContext
from solvexity.trader.model import Order
from solvexity.trader.core import SignalType
from solvexity.dependency.notification import Color
import time
import solvexity.helper as helper
import solvexity.helper.logging as logging
from pydantic import BaseModel
from threading import Thread

logger = logging.getLogger()

class StoppingOrder(BaseModel):
    symbol: str
    qty: Decimal
    side: str
    stop_upper_px: Decimal # logically easier than stop_loss_px/stop_profit_px
    stop_lower_px: Decimal

    @classmethod
    def from_order(cls, symbol: str, side: str, px: Decimal, qty: Decimal, stop_profit_pct: Decimal, stop_loss_pct: Decimal):
        one = Decimal('1')
        if side == 'BUY':
            stop_side = 'SELL'
            qty, stop_upper_px = helper.symbol_filter(symbol, qty, px * (one + stop_profit_pct))
            qty, stop_lower_px = helper.symbol_filter(symbol, qty, px * (one - stop_loss_pct))
            return cls(symbol=symbol, qty=qty, side=stop_side, stop_upper_px=stop_upper_px, stop_lower_px=stop_lower_px)
        elif side == 'SELL':
            stop_side = 'BUY'
            qty, stop_upper_px = helper.symbol_filter(symbol, one, px * (one + stop_loss_pct))
            qty, stop_lower_px = helper.symbol_filter(symbol, one, px * (one - stop_profit_pct))
            return cls(symbol=symbol, qty=qty, side=stop_side, stop_upper_px=stop_upper_px, stop_lower_px=stop_lower_px)
        else:
            raise ValueError(f"Unknown side {side}")

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
                 trade_id: str):
        super().__init__(trade_context, trade_id)
        self.symbol: str = symbol
        self.quote_size = Decimal(quote_size)
        self.stop_loss_pct = Decimal(profit_quote / quote_size)
        self.stop_profit_pct = Decimal(loss_quote / quote_size)
        self._order_id = 0
        
        self.hooks: dict[int, StoppingOrder] = {}
        self._px_react_thread = Thread(target=self._px_react_thread) 
        self._is_running = True

    @property
    def base(self):
        return self.symbol[:-4] # e.g. BTCUSDT -> BTC
    
    @property
    def quote(self):
        return self.symbol[-4:] # e.g. BTCUSDT -> USDT
    
    def _px_react_thread(self):
        for _ in self.trade_context.recv(): # To fit feed's recv instead of request every second
            dealt_orders = []
            ask, bid = self.trade_context.get_askbid(self.symbol)
            for order_id, order in self.hooks.items():
                if order.side == 'BUY' and ask >= order.stop_upper_px:
                    logger.info(f"Stop loss triggered for order {order_id}")
                    self.trade_context.market_buy(self.symbol, order.qty)
                    dealt_orders.append(order_id)
                elif order.side == 'BUY' and ask <= order.stop_lower_px:
                    logger.info(f"Stop profit triggered for order {order_id}")
                    self.trade_context.market_buy(self.symbol, order.qty)
                    dealt_orders.append(order_id)
                elif order.side == 'SELL' and bid >= order.stop_upper_px:
                    logger.info(f"Stop profit triggered for order {order_id}")
                    self.trade_context.market_sell(self.symbol, order.qty)
                elif order.side == 'SELL' and bid <= order.stop_lower_px:
                    logger.info(f"Stop loss triggered for order {order_id}")
                    self.trade_context.market_sell(self.symbol, order.qty)
            for order_id in dealt_orders:
                self.hooks.pop(order_id)                     
    
    def act(self, signal: SignalType):
        ask, bid = self.trade_context.get_askbid(self.symbol)
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
            logger.info(f"Sell {size} {self.symbol} at {px}")
            res = self.trade_context.market_buy(self.symbol, size)
            self.hooks[self._order_id] = StoppingOrder(symbol=self.symbol, qty=size, side='SELL', 
                                                       stop_upper_px=px * (Decimal('1') + self.stop_loss_pct), 
                                                       stop_lower_px=px * (Decimal('1') - self.stop_profit_pct))
            
            logger.info(f"Order response: {res}")
        except Exception as e:
            logger.error(f"Market sell failed: {e}", exc_info=True)

    def sell(self, px):
        try:
            size, px = helper.symbol_filter(self.symbol, self.quote_size / px, px)
            logger.info(f"Sell {size} {self.symbol} at {px}")
            res = self.trade_context.market_sell(self.symbol, size)
            logger.info(f"Order response: {res}")
        except Exception as e:
            logger.error(f"Market sell failed: {e}", exc_info=True)

    def close(self):
        self._is_running = False
        if self._px_react_thread.is_alive():
            self._px_react_thread.join()
        super().close()
    

    
    