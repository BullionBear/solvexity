from abc import ABC, abstractmethod

from solvexity.model.enum import Side, OrderType, TimeInForce, Symbol, Exchange
from typing import Type


class ExchangeAdapter(ABC):
    @abstractmethod
    async def __aenter__(self):
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    async def create_limit_order(self, symbol: Symbol, side: Side, quantity: float, price: float, time_in_force: TimeInForce):
        pass

    @abstractmethod
    async def create_market_order(self, symbol: Symbol, side: Side, quantity: float):
        pass

class ExchangeAdapterFactory:
    EXCHANGE_ADAPTER_MAP = {}
    def __init__(self, exchange: Exchange, **kwargs):
        self.exchange = exchange
    
    @classmethod
    def register_adapter(cls, exchange: Exchange, adapter: Type[ExchangeAdapter]):
        cls.EXCHANGE_ADAPTER_MAP[exchange] = adapter

    async def create_adapter(self, **kwargs):
        if self.exchange == Exchange.BINANCE:
            return NotImplementedError("Binance not supported")
        elif self.exchange == Exchange.BINANCE_PERP:
            raise NotImplementedError("Binance futures not supported")
        elif self.exchange == Exchange.BYBIT:
            raise NotImplementedError("Bybit not supported")
        else:
            raise ValueError(f"Exchange {self.exchange} not supported")