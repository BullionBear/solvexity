from abc import ABC, abstractmethod
from decimal import Decimal
from solvexity.trader.model import KLine, Trade
from solvexity.dependency.notification import Color
from typing import Optional
import solvexity.helper.logging as logging

logger = logging.getLogger()

class TradeContext(ABC):
    @abstractmethod
    def market_buy(self, symbol: str, size: Decimal):
        pass

    @abstractmethod
    def market_sell(self, symbol: str, size: Decimal):
        pass

    @abstractmethod
    def limit_buy(self, symbol: str, size: Decimal, price: Decimal)->str:
        pass

    @abstractmethod
    def limit_sell(self, symbol: str, size: Decimal, price: Decimal)->str:
        pass

    @abstractmethod
    def get_order(self, order_id: str):
        pass

    @abstractmethod
    def cancel_order(self, symbol: str, order_id: str):
        pass

    @abstractmethod
    def get_balance(self, token: str) -> Decimal:
        pass

    @abstractmethod
    def get_avaliable_balance(self, token: str) -> Decimal:
        pass

    @abstractmethod
    def get_askbid(self, symbol: str) -> tuple[Decimal, Decimal]:
        pass

    @abstractmethod
    def get_klines(self, symbol: str, limit: int, granular: str) -> list[KLine]:
        pass
    
    @abstractmethod
    def get_trades(self, symbol: str, limit: int) -> list[Trade]:
        pass

    @abstractmethod
    def recv(self):
        pass

    @abstractmethod
    def notify(self, username: str, title: str, content: Optional[str], color: Color):
        pass

    @abstractmethod
    def close(self):
        pass

    


class PerpTradeContext(TradeContext):
    @abstractmethod
    def get_positions(self, symbol: str):
        pass

    @abstractmethod
    def get_leverage_ratio(self, symbol: str):
        pass

