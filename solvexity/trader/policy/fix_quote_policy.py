from decimal import Decimal
from typing import Type
from solvexity.trader.core import Policy, TradeContext
from solvexity.trader.core import SignalType
from solvexity.dependency.notification import Color
import pandas as pd
import solvexity.helper as helper
import solvexity.helper.logging as logging

logger = logging.get_logger()

class FixQuotePolicy(Policy):
    """
        A policy that buy/sell fix quote size of the base asset.
    """
    MAX_TRADE_SIZE = 65535
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
    
    def act(self, signal: SignalType):
        if signal == SignalType.BUY:
            self.buy()
        elif signal == SignalType.SELL:
            self.sell()
        elif signal == SignalType.HOLD:
            pass
        else:
            logger.error(f"Unknown signal type {signal}", exc_info=True)
    
    def buy(self):
        logger.info(f"Buying {self.quote_size} {self.quote} for {self.symbol}")
        ask, _ = self.trade_context.get_askbid(self.symbol)
        try:
            size, ask = helper.symbol_filter(self.symbol, self.quote_size / ask, ask)
            logger.info(f"Buy {size} {self.symbol} at {ask}")
            res = self.trade_context.market_buy(self.symbol, size)
            logger.info(f"Order response: {res}")
        except Exception as e:
            logger.error(f"Market Buy failed: {e}", exc_info=True)
        

    def sell(self):
        logger.info(f"Selling {self.quote_size} {self.quote} for {self.symbol}")
        _, bid = self.trade_context.get_askbid(self.symbol)
        try:
            size, bid = helper.symbol_filter(self.symbol, self.quote_size / bid, bid)
            logger.info(f"Sell {size} {self.symbol} at {bid}")
            res = self.trade_context.market_sell(self.symbol, size)
            logger.info(f"Order response: {res}")
        except Exception as e:
            logger.error(f"Market Sell failed: {e}", exc_info=True)
        
       

    def export(self, output_dir: str):
        trades = self.trade_context.get_trades(self.symbol, self.MAX_TRADE_SIZE)
        df = pd.DataFrame([trade.dict() for trade in trades])
        logger.info(f"Exporting policy {self.symbol} trades to {output_dir}")
        target_dest = f"{output_dir}/policy_{self.symbol}_{self.id}.csv"
        df.to_csv(target_dest, index=False)
        

    def notify(self, title: str, content: str, color: Color):
        super().notify(title, content, color)
    
    def close(self):
        super().close()