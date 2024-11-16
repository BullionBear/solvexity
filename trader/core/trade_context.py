from abc import ABC, abstractmethod
from decimal import Decimal
import redis
from trader.data import query_latest_kline, KLine, query_kline, Trade
import helper.logging as logging
import binance.client as BinanceClient
from datetime import datetime, timezone
import helper

logger = logging.getLogger("trading")

class TradeContext(ABC):
    @abstractmethod
    def market_buy(self, symbol: str, size: Decimal):
        pass

    @abstractmethod
    def market_sell(self, symbol: str, size: Decimal):
        pass

    @abstractmethod
    def get_balance(self, token: str) -> Decimal:
        pass

    @abstractmethod
    def get_askbid(self, symbol: str) -> tuple[Decimal, Decimal]:
        pass

    @abstractmethod
    def get_klines(self, symbol: str, limit: int) -> list[KLine]:
        pass

    @abstractmethod
    def notify(self, **kwargs):
        pass
    
    @abstractmethod
    def get_trades(self, symbol: str, limit: int) -> list[Trade]:
        pass

    

class PaperTradeContext(TradeContext):
    """
    A paper trade context for trading strategies.  The execution of trades is simulated in this context in simple strategies.
    """
    def __init__(self, redis: redis.Redis, init_balance: dict[str, str], granular: str):
        """
        Args:
            init_balance (dict): The initial balance for the backtest context, e.g. {"BTC": '1', "USDT": '10000'}
            granular (str): The granularity of the kline data, e.g. "1m", "1h"
            redis (redis.Redis): The Redis client instance for querying kline data
        """
        self.granular = granular
        self.balance = {k: Decimal(v) for k, v in init_balance.items()}
        logger.info(f"Initial balance: {self.balance}\t Granular: {self.granular}")
        self.redis = redis
        self._trade_id = 1
        self.trade: list[Trade] = []

    def market_buy(self, symbol: str, size: Decimal):
        ask, _ = self.get_askbid(symbol)
        base, quote = symbol[:-4], symbol[-4:] # e.g. BTCUSDT -> BTC, USDT
        self.balance[base] += size
        self.balance[quote] -= size * ask
        logger.info(f"Market buy: {symbol}, size: {size}, price: {ask}")
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
        base, quote = symbol[:-4], symbol[-4:]
        self.balance[base] -= size
        self.balance[quote] += size * bid
        logger.info(f"Market sell: {symbol}, size: {size}, price: {bid}")
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
        return self.balance[token]

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
    
    def notify(self, **kwargs):
        content = [f'{key} = {value}' for key, value in kwargs.items()]
        content = '\t'.join(content)
        content = content.replace("\n", ", ")
        logger.info(f"Notification: {content}")

    def get_klines(self, symbol, limit) -> list[KLine]:
        lastest_kline = query_latest_kline(self.redis, symbol, self.granular)
        if not lastest_kline:
            raise ValueError(f"No kline data found: {symbol}:{self.granular}")
        ts = lastest_kline.close_time
        grandular_ts = helper.to_unixtime_interval(self.granular) * 1000
        end_ts = ts // grandular_ts * grandular_ts
        start_ts = end_ts - grandular_ts * limit
        klines = query_kline(self.redis, symbol, self.granular, start_ts, end_ts)
        return klines
    
    def get_trades(self, symbol, limit) -> list[Trade]:
        trades = filter(lambda x: x.symbol == symbol, self.trade)
        return list(trades)[-limit:]

class LiveTradeContext(TradeContext):
    def __init__(self, client: BinanceClient, redis: redis.Redis, webhook_url: str, granular: str):
        self.granular = granular
        self.client = client
        self.redis = redis
        self.webhook_url = webhook_url
        self.balance = self._get_balance()
        self.trade: dict[int, Trade] = {}

    def _get_balance(self):
        user_assets = self.client.get_user_asset(needBtcValuation=True)
        balance = {}
        for asset in user_assets:
            balance[asset['asset']] = str(Decimal(asset['free']) + Decimal(asset['locked']))
        return balance
    
    def get_balance(self, token: str) -> Decimal:
        return Decimal(self.balance.get(token, '0'))


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
                self.trade[trade['orderId']] = trade
        logger.info(f"Updated {n_trade} new trades for {symbol}")
    
    def notify(self, **kwargs):
        family = kwargs.get("family", "Notification")
        kwargs.pop("family", None)
        helper.send_notification(self.webhook_url, None, family, kwargs)

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
