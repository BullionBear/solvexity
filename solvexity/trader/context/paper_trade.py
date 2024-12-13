from typing import Optional
from decimal import Decimal
import redis
from solvexity.dependency.notification import Notification, Color
from solvexity.trader.core import TradeContext, Feed
from solvexity.trader.model import KLine, Trade
import solvexity.helper.logging as logging
from datetime import datetime, timezone
import solvexity.helper as helper

logger = logging.getLogger()

class PaperTradeSpotContext(TradeContext):
    """
    A paper trade context for trading strategies.  The execution of trades is simulated in this context in simple strategies.
    """
    def __init__(self, feed: Feed, notification: Notification,  init_balance: dict[str, str]):
        """
        Args:
            init_balance (dict): The initial balance for the backtest context, e.g. {"BTC": '1', "USDT": '10000'}
            redis (redis.Redis): The Redis client instance for querying kline data
        """
        self.balance = {k: {"free": Decimal(v), "locked": Decimal('0')} for k, v in init_balance.items()}
        logger.info(f"Initial balance: {self.balance}")
        self.feed: Feed = feed
        self.notification = notification
        self._trade_id = 1
        self.trade: list[Trade] = []

    def market_buy(self, symbol: str, size: Decimal):
        ask, _ = self.get_askbid(symbol)
        size, ask = helper.symbol_filter(symbol, size, ask)
        base, quote = symbol[:-4], symbol[-4:] # e.g. BTCUSDT -> BTC, USDT
        self.balance[base]['free'] += size
        self.balance[quote]['free'] -= size * ask
        logger.info(f"Market buy: {symbol}, size: {str(size)}, price: {str(ask)}")
        logger.info(f"Current balance: {self.balance}")
        self.trade.append(Trade(symbol=symbol, 
                                id=self._trade_id, 
                                order_id=self._trade_id, 
                                order_list_id=-1, 
                                price=float(ask), 
                                qty=float(size), 
                                quote_qty=float(size * ask), 
                                commission=0, 
                                commission_asset="BNB", 
                                time=self._get_time(), 
                                is_buyer=True, 
                                is_maker=False, 
                                is_best_match=True))
        self._trade_id += 1

    def market_sell(self, symbol: str, size: Decimal):
        _, bid = self.get_askbid(symbol)
        size, bid = helper.symbol_filter(symbol, size, bid)
        base, quote = symbol[:-4], symbol[-4:]
        self.balance[base]['free'] -= size
        self.balance[quote]['free'] += size * bid
        logger.info(f"Market sell: {symbol}, size: {str(size)}, price: {str(bid)}")
        logger.info(f"Current balance: {self.balance}")
        self.trade.append(Trade(symbol=symbol, 
                                id=self._trade_id, 
                                order_id=self._trade_id, 
                                order_list_id=-1, 
                                price=float(bid), 
                                qty=float(size), 
                                quote_qty=float(size * bid), 
                                commission=0, 
                                commission_asset="BNB", 
                                time=self._get_time(), 
                                is_buyer=False, 
                                is_maker=False, 
                                is_best_match=True))
        self._trade_id += 1

    def get_balance(self, token: str) -> Decimal:
        return self.balance[token]['free'] + self.balance[token]['locked']
    
    def get_avaliable_balance(self, token: str) -> Decimal:
        return self.balance[token]['free']

    def _get_time(self) -> int:
        return self.feed.time()
        
    def get_askbid(self, symbol: str) -> tuple[Decimal, Decimal]:
        lastest_kline = self.feed.latest_n_klines(symbol, '1m', 1)[0]
        return Decimal(lastest_kline.close), Decimal(lastest_kline.close)
    
    def notify(self, username: str, title: str, content: Optional[str], color: Color):
        self.notification.notify(username, title, content, color, self.feed.time())

    def get_klines(self, symbol: str, limit: int, granular: str) -> list[KLine]:
        return self.feed.latest_n_klines(symbol, granular, limit)
    
    def get_trades(self, symbol, limit) -> list[Trade]:
        trades = filter(lambda x: x.symbol == symbol, self.trade)
        return list(trades)[-limit:]
    