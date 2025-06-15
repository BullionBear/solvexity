from typing import Any, Dict, Type

from solvexity.connector.base import ExchangeConnector, ExchangeStreamConnector
from solvexity.connector.binance.adapter import (BinanceRestAdapter,
                                                 BinanceWebSocketAdapter)
from solvexity.connector.types import Exchange


class ExchangeConnectorFactory:
    @classmethod
    def create_rest_connector(
        self, exchange: Exchange, config: Dict[str, Any]
    ) -> Type[ExchangeConnector]:
        """
        Create a REST connector for the specified exchange.

        Args:
            exchange: The exchange to create a connector for
            config: A dictionary containing connector-specific configuration
                parameters
                For Binance: {
                    'api_key': str, 'api_secret': str, 'use_testnet': bool
                }
                For Bybit: {
                    'api_key': str, 'api_secret': str, 'use_testnet': bool
                }
        """
        if exchange == Exchange.BINANCE:
            return BinanceRestAdapter(
                api_key=config["api_key"],
                api_secret=config["api_secret"],
                use_testnet=config.get("use_testnet", False),
            )
        elif exchange == Exchange.BINANCE_FUTURES:
            raise NotImplementedError("Binance futures not implemented")
        elif exchange == Exchange.BYBIT:
            raise NotImplementedError("Bybit not implemented")
        raise ValueError(f"Unsupported exchange: {exchange}")

    @classmethod
    def create_websocket_connector(
        self, exchange: Exchange, config: Dict[str, Any]
    ) -> Type[ExchangeStreamConnector]:
        """
        Create a WebSocket connector for the specified exchange.

        Args:
            exchange: The exchange to create a connector for
            config: A dictionary containing connector-specific configuration
                parameters
                For Binance: {
                    'api_key': str, 'api_secret': str, 'use_testnet': bool
                }
                For Bybit: {
                    'api_key': str, 'api_secret': str, 'use_testnet': bool
                }
        """
        if exchange == Exchange.BINANCE:
            return BinanceWebSocketAdapter(
                api_key=config["api_key"],
                api_secret=config["api_secret"],
                use_testnet=config.get("use_testnet", False),
            )
        elif exchange == Exchange.BINANCE_FUTURES:
            raise NotImplementedError("Binance futures not implemented")
        elif exchange == Exchange.BYBIT:
            raise NotImplementedError("Bybit not implemented")
        raise ValueError(f"Unsupported exchange: {exchange}")
