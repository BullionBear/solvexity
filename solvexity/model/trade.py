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
        """Create Trade instance from protobuf Trade object"""
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

    @classmethod
    def from_protobuf_bytes(cls, data: bytes) -> 'Trade':
        """Create Trade instance directly from protobuf bytes
        
        This method encapsulates the two-step process of:
        1. Deserializing protobuf data from bytes
        2. Converting to Trade instance
        
        Args:
            data: Raw protobuf bytes
            
        Returns:
            Trade instance
            
        Raises:
            Exception: If protobuf parsing fails
        """
        pb_trade = pb2_trade.Trade()
        pb_trade.ParseFromString(data)
        return cls.from_protobuf(pb_trade)

    def to_protobuf(self) -> pb2_trade.Trade:
        """Convert Trade instance to protobuf Trade object"""
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

    def to_protobuf_bytes(self) -> bytes:
        """Convert Trade instance directly to protobuf bytes
        
        Returns:
            Serialized protobuf bytes
        """
        return self.to_protobuf().SerializeToString()
