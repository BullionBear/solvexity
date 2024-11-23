from abc import ABC, abstractmethod
from decimal import Decimal
from trader.data import KLine, Trade
from service.notification import Color
from typing import Optional
import helper.logging as logging

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
    def notify(self, title: str, content: Optional[str], color: Color):
        pass
    
    @abstractmethod
    def get_trades(self, symbol: str, limit: int) -> list[Trade]:
        pass
