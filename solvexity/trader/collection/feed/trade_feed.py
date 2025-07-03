from hooklet.base import PubSub
from solvexity.connector.types import Symbol, Exchange
from typing import Callable
from typing import AsyncGenerator
from solvexity.connector import ExchangeConnectorFactory
import uuid
from solvexity.trader.payload import TradePayload
from hooklet.node.emmiter import Emitter
from hooklet.base import Msg

class TradeFeed(Emitter):
    def __init__(self, 
                 node_id: str,
                 pubsub: PubSub, 
                 symbol: str, 
                 router: Callable[[Msg], str | None],
                 exchange: str 
                 ):
        super().__init__(node_id, pubsub, router)
        self.exchange = Exchange(exchange)
        self.rest_connector = ExchangeConnectorFactory.create_rest_connector(self.exchange, {"use_testnet": False})
        self.stream_connector = ExchangeConnectorFactory.create_websocket_connector(self.exchange, {"use_testnet": False})
        self.seq_id = 0
        self.symbol = Symbol.from_str(symbol)

        self._n_reconnects = 0
        self._n_data = 0

    async def emit(self) -> AsyncGenerator[Msg, None]:
        async for trade in self.stream_connector.public_trades_iterator(self.symbol):
            self.logger.info(f"Received Trade: {trade}")
            if self.seq_id == 0:
                self.seq_id = trade.id - 1 # mock the first trade
            if trade.id != self.seq_id + 1:
                self.logger.error(f"Trade ID mismatch: {trade.id} != {self.seq_id + 1}")
                self._n_reconnects += 1
                historical_trades = await self.rest_connector.get_recent_trades(self.symbol, limit=100)
                for historical_trade in historical_trades:
                    historical_trade_payload = TradePayload.from_trade(historical_trade)
                    if historical_trade.id == self.seq_id + 1:
                        self.seq_id = historical_trade.id
                        self._n_data += 1
                        yield Msg(
                            id=uuid.uuid4(),
                            type="trade",
                            data=historical_trade_payload,
                            error=None,
                        )
                    else:
                        continue
            else:
                self.seq_id = trade.id
                self._n_data += 1
                trade_payload = TradePayload.from_trade(trade)
                yield Msg(
                    id=uuid.uuid4(),
                    type="trade",
                    data=trade_payload,
                    error=None,
                )
    
