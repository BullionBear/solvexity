from abc import ABC, abstractmethod
from decimal import Decimal
import redis
from trader.data import query_latest_kline
import helper.logging as logging
import binance.client as BinanceClient
from datetime import datetime, timezone

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


class PaperTrade(TradeContext):
    """
    A paper trade context for trading strategies.  The execution of trades is simulated in this context in simple strategies.
    """
    def __init__(self, init_balance: dict[str, str], granular: str, redis: redis.Redis):
        """
        Args:
            init_balance (dict): The initial balance for the backtest context, e.g. {"BTC": '1', "USDT": '10000'}
            granular (str): The granularity of the kline data, e.g. "1m", "1h"
            redis (redis.Redis): The Redis client instance for querying kline data
        """
        self.ts = 0
        self.granular = granular
        self.balance = {k: Decimal(v) for k, v in init_balance.items()}
        logger.info(f"Initial balance: {self.balance}\n Granular: {self.granular}")
        self.redis = redis
        self.trade = []

    def market_buy(self, symbol: str, size: Decimal):
        ask, _ = self.get_askbid(symbol)
        base, quote = symbol[:-4], symbol[-4:] # e.g. BTCUSDT -> BTC, USDT
        self.balance[base] += size
        self.balance[quote] -= size * ask
        logger.info(f"Market buy: {symbol}, size: {size}, price: {ask}")
        logger.info(f"Current balance: {self.balance}")
        self.trade.append({"symbol": symbol, "size": str(size), "price": str(ask), "side": "sell"})

    def market_sell(self, symbol: str, size: Decimal):
        _, bid = self.get_askbid(symbol)
        base, quote = symbol[:-4], symbol[-4:]
        self.balance[base] -= size
        self.balance[quote] += size * bid
        logger.info(f"Market sell: {symbol}, size: {size}, price: {bid}")
        logger.info(f"Current balance: {self.balance}")
        self.trade.append({"symbol": symbol, "size": str(size), "price": str(bid), "side": "sell"})

    def get_balance(self, token: str) -> Decimal:
        return self.balance[token]
    
    def get_askbid(self, symbol: str):
        lastest_kline = query_latest_kline(self.redis, symbol, self.granular)
        self.ts = lastest_kline.close_time
        close_dt = datetime.fromtimestamp(self.ts // 1000, tz=timezone.utc)
        logger.info(f"Latest time: {close_dt.strftime('%Y-%m-%d %H:%M:%S')}, close: {lastest_kline.close}")
        return Decimal(lastest_kline.close), Decimal(lastest_kline.close)

class LiveTradeContext(TradeContext):
    def __init__(self, client: BinanceClient, granular: str, redis: redis.Redis):
        self.granular = granular
        self.client = client
        self.redis = redis
        self.balance = self._get_balance()

    def _get_balance(self):
        user_assets = self.client.get_user_asset(needBtcValuation=True)
        balance = {}
        for asset in user_assets:
            balance[asset['asset']] = str(Decimal(asset['free']) + Decimal(asset['locked']))
        return balance
    
    def get_balance(self, token: str) -> Decimal:
        return Decimal(self.balance[token])


    def market_buy(self, symbol: str, size: Decimal):
        self.client.order_market_buy(symbol=self.symbol, quantity=str(size))
        logger.info(f"Market sell: {symbol}, size: {size}, price: {bid}")
        logger.info(f"Current balance: {self.balance}")
