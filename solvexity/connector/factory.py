from abc import ABC, abstractmethod
from typing import Type

from solvexity.connector.binance.rest import BinanceRestConnector
from solvexity.connector.binance.websocket import BinanceWebSocketConnector
from solvexity.connector.types import Exchange, ExchangeRestConnector, ExchangeWebSocketConnector


class ExchangeConnectorFactory(ABC):
    
    def create_rest_connector(self, exchange: Exchange) -> Type[ExchangeRestConnector]:
        if exchange == Exchange.BINANCE:
            return BinanceRestConnector()
        elif exchange == Exchange.BINANCE_FUTURES:
            raise NotImplementedError("Binance futures not implemented")
        elif exchange == Exchange.BYBIT:
            raise NotImplementedError("Bybit not implemented")
        raise ValueError(f"Unsupported exchange: {exchange}")

    
    def create_websocket_connector(self, exchange: Exchange) -> Type[ExchangeWebSocketConnector]:
        if exchange == Exchange.BINANCE:
            return BinanceWebSocketConnector()
        elif exchange == Exchange.BINANCE_FUTURES:
            raise NotImplementedError("Binance futures not implemented")
        elif exchange == Exchange.BYBIT:
            raise NotImplementedError("Bybit not implemented")
        raise ValueError(f"Unsupported exchange: {exchange}")   
    