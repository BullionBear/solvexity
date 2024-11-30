from typing import Optional
from decimal import Decimal
import redis
from solvexity.dependency.notification import Notification, Color
from solvexity.trader.core import TradeContext
from solvexity.trader.data import query_latest_kline, KLine, query_kline, Trade
import solvexity.helper.logging as logging
from datetime import datetime, timezone
import solvexity.helper as helper

logger = logging.getLogger("trading")

class PaperTradeContext(TradeContext):
    """
    A paper trade context for trading strategies.  The execution of trades is simulated in this context in simple strategies.
    """
    def __init__(self, redis: redis.Redis, notification: Notification,  init_balance: dict[str, str], granular: str):
        """
        Args:
            init_balance (dict): The initial balance for the backtest context, e.g. {"BTC": '1', "USDT": '10000'}
            granular (str): The granularity of the kline data, e.g. "1m", "1h"
            redis (redis.Redis): The Redis client instance for querying kline data
        """
        self.granular = granular
        self.balance = {k: {"free": Decimal(v), "locked": Decimal('0')} for k, v in init_balance.items()}
        logger.info(f"Initial balance: {self.balance}\t Granular: {self.granular}")
        self.redis = redis
        self.notification = notification
        self._trade_id = 1
        self.trade: list[Trade] = []

    def market_buy(self, symbol: str, size: Decimal):
        ask, _ = self.get_askbid(symbol)
        size, ask = helper.symbol_filter(symbol, size, ask)
        base, quote = symbol[:-4], symbol[-4:] # e.g. BTCUSDT -> BTC, USDT
        self.balance[base]['free'] += size
        self.balance[quote]['free'] -= size * ask
        # self.notify("OnMarketBuy", f"Symbol: {symbol}\n size: {size}\n price: {ask}", Color.BLUE)
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
                                time=self._get_time(symbol), 
                                is_buyer=True, 
                                is_maker=False, 
                                is_best_match=True))
        self._trade_id += 1

    def market_sell(self, symbol: str, size: Decimal):
        _, bid = self.get_askbid(symbol)
        size, bid = helper.symbol_filter(symbol, size, bid)
        base, quote = symbol[:-4], symbol[-4:]
        self.balance[base]['free'] -= size
        self.balance[quote]['locked'] += size * bid
        # self.notify("OnMarketSell", f"Symbol: {symbol}\n size: {size}\n price: {bid}", Color.BLUE)
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
                                time=self._get_time(symbol), 
                                is_buyer=False, 
                                is_maker=False, 
                                is_best_match=True))
        self._trade_id += 1

    def get_balance(self, token: str) -> Decimal:
        return self.balance[token]['free'] + self.balance[token]['locked']
    
    def get_avaliable_balance(self, token: str) -> Decimal:
        return self.balance[token]['free']

    def _get_time(self, symbol: str) -> int:
        lastest_kline = query_latest_kline(self.redis, symbol, self.granular)
        if not lastest_kline:
            raise ValueError(f"No kline data found: {symbol}:{self.granular}")
        return lastest_kline.event_time
        
    
    def get_askbid(self, symbol: str) -> tuple[Decimal, Decimal]:
        lastest_kline = query_latest_kline(self.redis, symbol, self.granular)
        if not lastest_kline:
            raise ValueError(f"No kline data found: {symbol}:{self.granular}")
        ts = lastest_kline.close_time
        close_dt = datetime.fromtimestamp(ts // 1000, tz=timezone.utc)
        logger.info(f"Latest time: {close_dt.strftime('%Y-%m-%d %H:%M:%S')}, close: {lastest_kline.close}")
        return Decimal(lastest_kline.close), Decimal(lastest_kline.close)
    
    def notify(self, username: str, title: str, content: Optional[str], color: Color):
        self.notification.notify(username, title, content, color)

    def get_klines(self, symbol, limit) -> list[KLine]:
        lastest_kline = query_latest_kline(self.redis, symbol, self.granular)
        if not lastest_kline:
            logger.error(f"No kline data found: {symbol}:{self.granular}")
            return []
        end_ts = lastest_kline.close_time
        grandular_ts = helper.to_unixtime_interval(self.granular) * 1000
        start_ts = end_ts - grandular_ts * limit
        klines = query_kline(self.redis, symbol, self.granular, start_ts, end_ts)
        return klines
    
    def get_trades(self, symbol, limit) -> list[Trade]:
        trades = filter(lambda x: x.symbol == symbol, self.trade)
        return list(trades)[-limit:]