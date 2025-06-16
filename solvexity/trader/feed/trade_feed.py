from solvexity.connector.base import ExchangeStreamConnector
from hooklet.base import BasePilot
from hooklet.eventrix.v2.node import Node
from solvexity.connector.types import Symbol, Exchange
from typing import Callable
from hooklet.types import HookletMessage
from typing import AsyncGenerator
from solvexity.connector.base import ExchangeConnector
from solvexity.connector import ExchangeConnectorFactory
import uuid
import random
import time
from pydantic import Field
from typing import Any


class TradeFeed(Node):
    def __init__(self, 
                 exchange: Exchange,
                 pilot: BasePilot, 
                 symbol: Symbol, 
                 sources: list[str], 
                 router: Callable[[HookletMessage], str | None], 
                 node_id: None|str=None,
                 ):
        super().__init__(pilot, sources, router, node_id)
        self.rest_connector = ExchangeConnectorFactory.create_rest_connector(exchange, {})
        self.stream_connector = ExchangeConnectorFactory.create_websocket_connector(exchange, {})
        self.symbol = symbol

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
    
