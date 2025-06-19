from hooklet.base import BasePilot
from solvexity.connector.types import Symbol, Exchange, InstrumentType
from typing import Callable, Any
from hooklet.types import HookletMessage
from typing import AsyncGenerator
from solvexity.connector.base import ExchangeConnector, ExchangeStreamConnector
from solvexity.connector import ExchangeConnectorFactory
from pydantic import BaseModel
import uuid
import random
import time
from solvexity.trader.base import ConfigNode


class TradeFeedConfig(BaseModel):
    exchange: Exchange
    symbol: Symbol
    node_id: None|str=None
    use_testnet: bool = False

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "TradeFeedConfig":
        """
        Create a TradeFeedConfig from a configuration dictionary.
        Example:
        {
            "exchange": "BINANCE",
            "symbol": {"base_currency": "BTC", "quote_currency": "USDT", "instrument_type": "SPOT"},
            "node_id": "trade_feed",
            "use_testnet": false
        }
        """
        return cls(
            exchange=Exchange(config["exchange"]),
            symbol=Symbol(
                base_currency=config["symbol"]["base_currency"],
                quote_currency=config["symbol"]["quote_currency"],
                instrument_type=InstrumentType(config["symbol"]["instrument_type"]),
            ),
            node_id=config["node_id"],
            use_testnet=config.get("use_testnet", False)
        )

class TradeFeed(ConfigNode):
    def __init__(self, 
                 pilot: BasePilot, 
                 symbol: Symbol, 
                 router: Callable[[HookletMessage], str | None], 
                 node_id: None|str=None,
                 rest_connector: ExchangeConnector | None = None,
                 stream_connector: ExchangeStreamConnector | None = None,
                 ):
        super().__init__(pilot, [], router, node_id)
        self.rest_connector = rest_connector
        self.stream_connector = stream_connector
        self.symbol = symbol

    @classmethod
    def from_config(cls, pilot: BasePilot, config: dict[str, Any]) -> "TradeFeed":
        config_obj = TradeFeedConfig.from_config(config)
        def create_router_path(e):
            components = [
                e.node_id,
                e.type,
                config_obj.exchange.value,
                config_obj.symbol.base_currency,
                config_obj.symbol.quote_currency,
                config_obj.symbol.instrument_type.value
            ]
            return ".".join(components)
        rest_connector = ExchangeConnectorFactory.create_rest_connector(config_obj.exchange, {"use_testnet": config_obj.use_testnet})
        stream_connector = ExchangeConnectorFactory.create_websocket_connector(config_obj.exchange, {"use_testnet": config_obj.use_testnet})
        return cls(pilot, config_obj.symbol, create_router_path, config_obj.node_id, rest_connector, stream_connector)

    async def generator_func(self) -> AsyncGenerator[HookletMessage, None]:
        """
        Default generator function that yields nothing.
        Override this method to provide custom generator behavior.
        """
        async for trade in self.stream_connector.public_trades_iterator(self.symbol):
            timestamp = int(time.time() * 1000)
            self.logger.info(f"Received Trade: {trade}")
            yield HookletMessage(
                id=uuid.uuid4(),
                node_id=self.node_id,
                correlation_id=random.randint(0, 2**64 - 1),
                type="trade",
                payload=trade,
                start_at=timestamp,
                finish_at=timestamp,
            )
    
