from decimal import Decimal
import redis
from solvexity.trader.core import TradeContext
from solvexity.trader.core import Feed
from typing import Optional
from solvexity.dependency.notification import Notification, Color
from solvexity.trader.model import KLine, Trade
import solvexity.helper.logging as logging
from binance.client import Client
from solvexity.dependency.notification import Notification
import solvexity.helper as helper

logger = logging.getLogger()

class SpotTradeContext(TradeContext):
    def __init__(self, client: Client, feed: Feed, notification: Notification):
        self.client = client
        self.feed = feed
        self.notification = notification
        self.balance = self._get_balance()
        self.trade: dict[int, Trade] = {}

    def _get_balance(self):
        user_assets = self.client.get_user_asset(needBtcValuation=True)
        balance = {}
        for asset in user_assets:
            balance[asset['asset']] = {
                "free": Decimal(asset['free']),
                "locked": Decimal(asset['locked'])
            }
        logger.info(f"Current balance: {balance}")
        return balance
    
    def get_balance(self, token: str) -> Decimal:
        if token not in self.balance:
            return Decimal('0')
        return Decimal(self.balance[token]['free']) + Decimal(self.balance[token]['locked'])

    def get_avaliable_balance(self, token) -> Decimal:
        if token not in self.balance:
            return Decimal('0')
        return self.balance[token]['free']

    def market_buy(self, symbol: str, size: Decimal):
        try:
            _, bid = self.get_askbid(symbol)
            size, bid = helper.symbol_filter(symbol, size, bid)
            logger.info(f"Market buy: {symbol}, size: {size}")
            res = self.client.order_market_buy(symbol=symbol, quantity=str(size))
            logger.info(f"Order response: {res}")
            self.balance = self._get_balance()
        except Exception as e:
            logger.error(f"Market buy failed: {e}", exc_info=True)

    def market_sell(self, symbol: str, size: Decimal):
        try:
            ask, _ = self.get_askbid(symbol)
            size, ask = helper.symbol_filter(symbol, size, ask)
            logger.info(f"Market sell: {symbol}, size: {size}, expected price: {ask}")
            res = self.client.order_market_sell(symbol=symbol, quantity=str(size))
            logger.info(f"Order response: {res}")
            self.balance = self._get_balance()
        except Exception as e:
            logger.error(f"Market sell failed: {e}", exc_info=True)

    def limit_buy(self, symbol: str, size: Decimal, price: Decimal):
        try:
            size, price = helper.symbol_filter(symbol, size, price)
            logger.info(f"Limit buy: {symbol}, size: {size}, price: {price}")
            res = self.client.order_limit_buy(symbol=symbol, quantity=str(size), price=str(price))
            logger.info(f"Order response: {res}")
            self.balance = self._get_balance()
        except Exception as e:
            logger.error(f"Limit buy failed: {e}", exc_info=True)

    def limit_sell(self, symbol, size, price):
        try:
            size, price = helper.symbol_filter(symbol, size, price)
            logger.info(f"Limit sell: {symbol}, size: {size}, price: {price}")
            res = self.client.order_limit_sell(symbol=symbol, quantity=str(size), price=str(price))
            logger.info(f"Order response: {res}")
            self.balance = self._get_balance()
        except Exception as e:
            logger.error(f"Limit sell failed: {e}", exc_info=True)

    def cancel_order(self, order_id: str):
        try:
            logger.info(f"Cancel order: {order_id}")
            res = self.client.cancel_order(orderId=order_id)
            logger.info(f"Order response: {res}")
            self.balance = self._get_balance()
        except Exception as e:
            logger.error(f"Cancel order failed: {e}", exc_info=True)

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
        self.notification.notify(username, title, content, color, self.feed.time())


    def get_klines(self, symbol: str, limit: int, granular: str) -> list[KLine]:
        klines = self.feed.latest_n_klines(symbol, granular, limit)
        return klines
    
    def get_trades(self, symbol, limit) -> list[Trade]:
        self._update_trade(symbol)
        trades = filter(lambda x: x.symbol == symbol, self.trade.values())
        return sorted(trades, key=lambda t: t.id)[-limit:]
