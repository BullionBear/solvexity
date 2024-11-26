from decimal import Decimal
import redis
from trader.core import TradeContext
from typing import Optional
from dependency.notification import Notification, Color
from trader.data import query_latest_kline, KLine, query_kline, Trade
import helper.logging as logging
import binance.client as BinanceClient
from dependency.notification import Notification
import helper

logger = logging.getLogger("trading")

class SpotTradeContext(TradeContext):
    def __init__(self, client: BinanceClient, redis: redis.Redis, notification: Notification, granular: str):
        self.granular = granular
        self.client = client
        self.redis = redis
        self.notification = notification
        self.balance = self._get_balance()
        self.trade: dict[int, Trade] = {}

    def _get_balance(self):
        user_assets = self.client.get_user_asset(needBtcValuation=True)
        balance = {}
        for asset in user_assets:
            balance[asset['asset']] = {
                "free": Decimal(asset['free']),
                "lock": Decimal(asset['locked'])
            }
        return balance
    
    def get_balance(self, token: str) -> Decimal:
        if token not in self.balance:
            return Decimal('0')
        return Decimal(self.balance[token]['free']) + Decimal(self.balance[token]['locked'])

    def get_avaliable_balance(self, token):
        return Decimal(self.balance.get(token, '0')['free'])

    def market_buy(self, symbol: str, size: Decimal):
        self.client.order_market_buy(symbol=symbol, quantity=str(size))
        logger.info(f"Market buy: {symbol}, size: {size}")
        self.balance = self._get_balance()
        logger.info(f"Current balance: {self.balance}")

    def market_sell(self, symbol: str, size: Decimal):
        self.client.order_market_sell(symbol=symbol, quantity=str(size))
        logger.info(f"Market sell: {symbol}, size: {size}")
        self.balance = self._get_balance()
        logger.info(f"Current balance: {self.balance}")

    def get_askbid(self, symbol: str):
        order_book = self.client.get_order_book(symbol=symbol, limit=1)
        return Decimal(order_book['asks'][0][0]), Decimal(order_book['bids'][0][0])
    
    def _update_trade(self, symbol: str):
        trades = self.client.get_my_trades(symbol=symbol, limit=100)
        n_trade = 0
        for trade in trades:
            if trade['orderId'] not in self.trade:
                n_trade += 1
                self.trade[trade['orderId']] = Trade.from_rest(trade)
        logger.info(f"Updated {n_trade} new trades for {symbol}")
    
    def notify(self, username: str, title: str, content: Optional[str], color: Color):
        self.notification.notify(username, title, content, color)


    def get_klines(self, symbol, limit) -> list[KLine]:
        lastest_kline = query_latest_kline(self.redis, symbol, self.granular)
        if not lastest_kline:
            raise ValueError("No kline data found")
        ts = lastest_kline.close_time
        grandular_ts = helper.to_unixtime_interval(self.granular) * 1000
        end_ts = ts // grandular_ts * grandular_ts
        start_ts = end_ts - grandular_ts * limit
        klines = query_kline(self.redis, symbol, self.granular, start_ts, end_ts)
        return klines
    
    def get_trades(self, symbol, limit) -> list[Trade]:
        self._update_trade(symbol)
        trades = filter(lambda x: x['symbol'] == symbol, self.trade.values())
        return sorted(trades, key=lambda t: t.id)[-limit:]
