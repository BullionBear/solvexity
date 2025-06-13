from abc import ABC, abstractmethod
from typing import Type, Dict, Any

from solvexity.connector.binance.rest import BinanceRestConnector
from solvexity.connector.binance.websocket import BinanceWebSocketConnector
from solvexity.connector.types import Exchange, ExchangeRestConnector, ExchangeWebSocketConnector


class ExchangeConnectorFactory(ABC):
    
    def create_rest_connector(self, exchange: Exchange, config: Dict[str, Any]) -> Type[ExchangeRestConnector]:
        """
        Create a REST connector for the specified exchange.
        
        Args:
            exchange: The exchange to create a connector for
            config: A dictionary containing connector-specific configuration parameters
                   For Binance: {'api_key': str, 'api_secret': str, 'use_testnet': bool}
                   For Bybit: {'api_key': str, 'api_secret': str, 'passphrase': str, 'use_testnet': bool}
        """
        if exchange == Exchange.BINANCE:
            return BinanceRestConnector(
                api_key=config['api_key'],
                api_secret=config['api_secret'],
                use_testnet=config.get('use_testnet', False)
            )
        elif exchange == Exchange.BINANCE_FUTURES:
            raise NotImplementedError("Binance futures not implemented")
        elif exchange == Exchange.BYBIT:
            raise NotImplementedError("Bybit not implemented")
        raise ValueError(f"Unsupported exchange: {exchange}")

    
    def create_websocket_connector(self, exchange: Exchange, config: Dict[str, Any]) -> Type[ExchangeWebSocketConnector]:
        """
        Create a WebSocket connector for the specified exchange.
        
        Args:
            exchange: The exchange to create a connector for
            config: A dictionary containing connector-specific configuration parameters
                   For Binance: {'api_key': str, 'api_secret': str, 'use_testnet': bool}
                   For Bybit: {'api_key': str, 'api_secret': str, 'passphrase': str, 'use_testnet': bool}
        """
        if exchange == Exchange.BINANCE:
            return BinanceWebSocketConnector(
                api_key=config['api_key'],
                api_secret=config['api_secret'],
                use_testnet=config.get('use_testnet', False)
            )
        elif exchange == Exchange.BINANCE_FUTURES:
            raise NotImplementedError("Binance futures not implemented")
        elif exchange == Exchange.BYBIT:
            raise NotImplementedError("Bybit not implemented")
        raise ValueError(f"Unsupported exchange: {exchange}")   
    