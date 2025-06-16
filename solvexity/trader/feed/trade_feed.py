from solvexity.connector.base import ExchangeStreamConnector
from hooklet.base import BasePilot
from hooklet.eventrix.v2.node import Node
from solvexity.connector.types import Symbol, Exchange, InstrumentType
from typing import Callable
from hooklet.types import HookletMessage
from typing import AsyncGenerator
from solvexity.connector.base import ExchangeConnector, ExchangeStreamConnector
from solvexity.connector import ExchangeConnectorFactory
import uuid
import random
import time
from pydantic import Field
from typing import Any


class TradeFeed(Node):
    def __init__(self, 
                 pilot: BasePilot, 
                 symbol: Symbol, 
                 router: Callable[[HookletMessage], str | None], 
                 node_id: None|str=None,
                 rest_connector: ExchangeConnector | None = None,
                 stream_connector: ExchangeConnector | None = None,
                 ):
        super().__init__(pilot, [], router, node_id)
        self.rest_connector = rest_connector
        self.stream_connector = stream_connector
        self.symbol = symbol

    @classmethod
    def from_config(cls, pilot: BasePilot, config: dict[str, Any]) -> "TradeFeed":
        """
        Creates a TradeFeed instance from a configuration dictionary.

        Args:
            pilot (BasePilot): The pilot instance.
            config (dict[str, Any]): The configuration dictionary.

        Returns:
            TradeFeed: The created TradeFeed instance.
        """
        exchange = Exchange(config["exchange"])
        rest_connector = ExchangeConnectorFactory.create_rest_connector(config["exchange"], {config.get("credentials", {})})
        stream_connector = ExchangeConnectorFactory.create_websocket_connector(config["exchange"], {config.get("credentials", {})})
        symbol = Symbol(config["base_currency"], config["quote_currency"], InstrumentType(config["instrument_type"]))
        return cls(
            exchange=config["exchange"],
            pilot=pilot,
            symbol=config["symbol"],
            rest_connector=rest_connector,
            stream_connector=stream_connector,
        )

    async def generator_func(self) -> AsyncGenerator[HookletMessage, None]:
        """
        Default generator function that yields nothing.
        Override this method to provide custom generator behavior.
        """
        async for trade in self.stream_connector.execution_updates_iterator(self.symbol):
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
    
