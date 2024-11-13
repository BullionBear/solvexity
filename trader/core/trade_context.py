from abc import ABC, abstractmethod
from decimal import Decimal
import redis
from trader.data import query_latest_kline, get_key

class TradeContext(ABC):
    @abstractmethod
    def market_buy(self, symbol: str, size: float):
        pass

    @abstractmethod
    def market_sell(self, symbol: str, size: float):
        pass

    @abstractmethod
    def get_balance(self, token: str):
        pass

    @abstractmethod
    def get_askbid(self, symbol: str):
        pass


class BacktestContext(TradeContext):
    """
    A backtest context for trading strategies.  The execution of trades is simulated in this context in simple strategies.
    """
    def __init__(self, init_balance: dict, granular: str, redis: redis.Redis):
        """
        Args:
            init_balance (dict): The initial balance for the backtest context, e.g. {"BTC": '1', "USDT": '10000'}
        """
        self.ts = 0
        self.balance = {k: Decimal(v) for k, v in init_balance.items()}

    def market_buy(self, symbol: str, size: Decimal):
        ask, _ = self.get_askbid(symbol)
        base, quote = symbol[:-4], symbol[-4:] # e.g. BTCUSDT -> BTC, USDT
        self.balance[base] += size
        self.balance[quote] -= size * ask

    def market_sell(self, symbol: str, size: Decimal):
        _, bid = self.get_askbid(symbol)
        base, quote = symbol[:-4], symbol[-4:]
        self.balance[base] -= size
        self.balance[quote] += size * bid

    def get_balance(self, token: str):
        return self.balance[token]
    
    def get_askbid(self, symbol: str):
        lastest_kline = query_latest_kline(self.redis, symbol, "1m")
        return 

class PaperTradeContext(TradeContext):
    def __init__(self):
        pass

class LiveTradeContext(TradeContext):
    def __init__(self):
        pass
