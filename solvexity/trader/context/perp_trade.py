from decimal import Decimal
import redis
import time
from solvexity.trader.core import PerpTradeContext
from typing import Optional
from solvexity.dependency.notification import Notification, Color
from solvexity.trader.data import (
    query_latest_kline, query_kline, 
    KLine, Trade, Position
)
import solvexity.helper.logging as logging
import binance.client as BinanceClient
from solvexity.dependency.notification import Notification
import solvexity.helper

logger = logging.getLogger("trading")

class PerpTradeContext(PerpTradeContext):
    def __init__(self, client: BinanceClient, 
                 redis: redis.Redis, 
                 notification: Notification, 
                 granular: str, 
                 leverage: int):
        self.granular = granular
        self.client = client
        self.redis = redis
        self.notification = notification
        self.leverage = leverage
        self._symbol_with_leverage = set()
        self.balance = self._get_balance()
        self.trade: dict[int, Trade] = {}
        self.position: dict[str, Position] = {}
        

    def _get_balance(self):
        user_assets = self.client.futures_account_balance()
        balance = {}
        for asset in user_assets:
            free_balance = Decimal(asset['availableBalance'])
            total_balance = Decimal(asset['balance'])
            balance[asset['asset']] = {
                'free': str(free_balance),
                'locked': str(total_balance - free_balance)
            }
        return balance
    
    def get_balance(self, token: str) -> Decimal:
        return Decimal(self.balance.get(token, '0'))
    
    def _set_leverage(self, symbol: str, leverage: int):
        if symbol in self._symbol_with_leverage:
            return
        self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
        self._symbol_with_leverage.add(symbol)
        logger.info(f"Set leverage for {symbol} to {leverage}")


    def market_buy(self, symbol: str, size: Decimal):
        self._set_leverage(symbol, self.leverage)
        self.client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=size)
        logger.info(f"Market buy: {symbol}, size: {size}")
        self.balance = self._get_balance()
        logger.info(f"Current balance: {self.balance}")

    def market_sell(self, symbol: str, size: Decimal):
        self._set_leverage(symbol, self.leverage)
        self.client.futures_create_order(symbol=symbol, side='BUY', type='MARKET', quantity=size)
        logger.info(f"Market sell: {symbol}, size: {size}")
        self.balance = self._get_balance()
        logger.info(f"Current balance: {self.balance}")

    def get_askbid(self, symbol: str):
        order_book = self.client.futures_order_book(symbol=symbol, limit=1)
        return Decimal(order_book['asks'][0][0]), Decimal(order_book['bids'][0][0])
    
    def _update_trade(self, symbol: str):
        trades = self.client.futures_account_trades(symbol=symbol, limit=1)
        n_trade = 0
        for trade in trades:
            if trade['orderId'] not in self.trade:
                n_trade += 1
                self.trade[trade['orderId']] = Trade.from_perp_rest(trade)
        logger.info(f"Updated {n_trade} new trades for {symbol}")

    def _update_position(self):
        positions = self.client.futures_position_information()
        for position in positions:
            symbol = position['symbol']
            self.position[symbol] = Position.from_perp_rest(position)
    
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
    
    def get_positions(self) -> list[Position]:
        self._update_position()
        return self.position
    
    def get_leverage_ratio(self) -> Decimal:
        usdt = self.get_balance('USDT')
        position_value = sum([Decimal(pos['positionAmt']) * Decimal(pos['entryPrice']) for pos in self.get_positions().values()])
        return position_value / usdt
        
        

