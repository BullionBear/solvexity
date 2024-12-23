from decimal import Decimal
from typing import Type
from solvexity.trader.core import Policy, TradeContext
from solvexity.trader.core import SignalType
from solvexity.dependency.notification import Color
import pandas as pd
import solvexity.helper as helper
import solvexity.helper.logging as logging

logger = logging.getLogger()

class FixBasePolicy(Policy):
    """
        A policy that buy/sell fix base size of the U-Perp
    """
    MAX_TRADE_SIZE = 65535
    def __init__(self, trade_context: Type[TradeContext], symbol: str, base_size: float, is_reversed: bool, trade_id: str):
        super().__init__(trade_context, trade_id)
        self.symbol: str = symbol
        self.base_size = Decimal(base_size)

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
        ask, _ = self.trade_context.get_askbid(self.symbol)
        try:
            logger.info(f"{self.__class__.__name__}: {self.id} Buy {self.size} {self.symbol} at {ask}")
            res = self.trade_context.market_buy(self.symbol, self.base_size)
            content = helper.to_content({
                "policy": self.__class__.__name__,
                "trade id": self.id,
                "symbol": self.symbol,
                "size": self.size,
                "ref price": ask
            })
            self.notify("OnMarketBuy", content, Color.GREEN)
            logger.info(f"Order response: {res}")
        except Exception as e:
            logger.error(f"Market long failed: {e}", exc_info=True)


    def sell(self):
        _, bid = self.trade_context.get_askbid(self.symbol)
        try:
            logger.info(f"Sell {self.size} {self.symbol} at {bid}")
            res = self.trade_context.market_sell(self.symbol, self.base_size)
            content = helper.to_content({
                "policy": self.__class__.__name__,
                "trade id": self.id,
                "symbol": self.symbol,
                "size": self.size,
                "ref price": bid
            })
            self.notify("OnMarketSell", content, Color.RED)
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