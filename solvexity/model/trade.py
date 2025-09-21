import solvexity.model.protobuf.trade_pb2 as pb2_trade
from pydantic import BaseModel
from typing import Optional
from .shared import Symbol, Exchange, Instrument, Side


class Trade(BaseModel):
    id: int
    exchange: Exchange
    instrument: Instrument
    symbol: Symbol
    side: Side
    price: float
    quantity: float
    timestamp: int

    @classmethod
    def from_protobuf(cls, trade: pb2_trade.Trade) -> 'Trade':
        return cls(
            id=trade.id,
            exchange=Exchange.from_protobuf(trade.exchange),
            instrument=Instrument.from_protobuf(trade.instrument),
            symbol=Symbol.from_protobuf(trade.symbol),
            side=Side.from_protobuf(trade.side),
            price=trade.price,
            quantity=trade.quantity,
            timestamp=trade.timestamp,
        )

    def to_protobuf(self) -> pb2_trade.Trade:
        trade = pb2_trade.Trade()
        trade.id = self.id
        trade.exchange = self.exchange.to_protobuf()
        trade.instrument = self.instrument.to_protobuf()
        trade.symbol.CopyFrom(self.symbol.to_protobuf())
        trade.side = self.side.to_protobuf()
        trade.price = self.price
        trade.quantity = self.quantity
        trade.timestamp = self.timestamp
        return trade
