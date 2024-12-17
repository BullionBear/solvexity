from decimal import Decimal
from typing import Type
from solvexity.trader.core import Policy, TradeContext
from solvexity.trader.context.perp_trade import PerpTradeContext
from solvexity.trader.model import Trade
from solvexity.dependency.notification import Color
import pandas as pd
import solvexity.helper as helper
import solvexity.helper.logging as logging

logger = logging.getLogger()

class FixBasePerpPolicy(Policy):
    """
        A policy that buy/sell fix base size of the U-Perp
    """
    MAX_TRADE_SIZE = 65535
    def __init__(self, trade_context: Type[PerpTradeContext], symbol: str, base_size: float, is_reversed: bool, trade_id: str):
        super().__init__(trade_context, trade_id)
        self.symbol: str = symbol
        self.base_size = Decimal(base_size)
        self.is_reversed = is_reversed
        self.position: int = 0

    @property
    def base(self):
        return self.symbol[:-4] # e.g. BTCUSDT -> BTC
    
    @property
    def quote(self):
        return self.symbol[-4:] # e.g. BTCUSDT -> USDT
    
    def buy(self):
        ask, _ = self.trade_context.get_askbid(self.symbol)
        try:
            sz = self.base_size
            self.position += 1
            if self.is_reversed and self.position == 0:
                sz += self.base_size
                self.position = 1
            logger.info(f"Long {self.size} {self.symbol} at {ask}")
            self.notify("OnMarketLong", f"**Trade ID**: {self.id}\n**Symbol**: {self.symbol}\n**size**: {sz}\n**ref price**: {ask}", Color.MAGENTA)
            res = self.trade_context.market_buy(self.symbol, self.base_size)
            logger.info(f"Order response: {res}")
        except Exception as e:
            logger.error(f"Market long failed: {e}", exc_info=True)


    def sell(self):
        logger.info(f"Short {self.base_size} {self.base}")
        _, bid = self.trade_context.get_askbid(self.symbol)
        
        try:
            sz = self.base_size
            self.position -= 1
            if self.is_reversed and self.position == 0:
                sz += self.base_size
                self.position = -1
            logger.info(f"Short{self.size} {self.symbol} at {bid}")
            self.notify("OnMarketShort", f"**Trade ID**: {self.id}\n**Symbol**: {self.symbol}\n**size**: {sz}\n**ref price**: {bid}", Color.MAGENTA)
            res = self.trade_context.market_sell(self.symbol, sz)
            logger.info(f"Order response: {res}")
        except Exception as e:
            logger.error(f"Market short failed: {e}", exc_info=True)

    def export(self, output_dir: str):
        trades = self.trade_context.get_trades(self.symbol, self.MAX_TRADE_SIZE)
        df = pd.DataFrame([trade.dict() for trade in trades])
        logger.info(f"Exporting policy {self.symbol} trades to {output_dir}")
        target_dest = f"{output_dir}/policy_{self.symbol}_{self.id}.csv"
        df.to_csv(target_dest, index=False)
        

    def notify(self, title: str, content: str, color: Color):
        super().notify(title, content, color)