import solvexity.model.protobuf.shared_pb2 as pb2_shared
from pydantic import BaseModel
from enum import IntEnum

class Symbol(BaseModel):
    base: str
    quote: str

    @classmethod
    def from_protobuf(cls, symbol: pb2_shared.Symbol) -> 'Symbol':
        return cls(base=symbol.base, quote=symbol.quote)

    def to_protobuf(self) -> pb2_shared.Symbol:
        return pb2_shared.Symbol(base=self.base, quote=self.quote)

class Instrument(IntEnum):
    INSTRUMENT_UNSPECIFIED = 0
    INSTRUMENT_SPOT = 1
    INSTRUMENT_MARGIN = 2
    INSTRUMENT_PERP = 3
    INSTRUMENT_INVERSE = 4
    INSTRUMENT_FUTURES = 5
    INSTRUMENT_OPTION = 6

    @classmethod
    def from_protobuf(cls, instrument: pb2_shared.Instrument) -> 'Instrument':
        return cls(instrument)

    def to_protobuf(self) -> int:
        return self.value


class Exchange(IntEnum):
    EXCHANGE_UNSPECIFIED = 0
    EXCHANGE_BINANCE = 1
    EXCHANGE_BINANCE_PERP = 2
    EXCHANGE_BYBIT = 3

    @classmethod
    def from_protobuf(cls, exchange: pb2_shared.Exchange) -> 'Exchange':
        return cls(exchange)

    def to_protobuf(self) -> int:
        return self.value


class Side(IntEnum):
    SIDE_UNSPECIFIED = 0
    SIDE_BUY = 1
    SIDE_SELL = 2

    @classmethod
    def from_protobuf(cls, side: pb2_shared.Side) -> 'Side':
        return cls(side)

    def to_protobuf(self) -> int:
        return self.value


class TimeInForce(IntEnum):
    TIME_IN_FORCE_UNSPECIFIED = 0
    TIME_IN_FORCE_GTC = 1
    TIME_IN_FORCE_IOC = 2
    TIME_IN_FORCE_FOK = 3

    @classmethod
    def from_protobuf(cls, time_in_force: pb2_shared.TimeInForce) -> 'TimeInForce':
        return cls(time_in_force)

    def to_protobuf(self) -> int:
        return self.value


class OrderType(IntEnum):
    ORDER_TYPE_UNSPECIFIED = 0
    ORDER_TYPE_LIMIT = 1
    ORDER_TYPE_MARKET = 2
    ORDER_TYPE_STOP_MARKET = 3

    @classmethod
    def from_protobuf(cls, order_type: pb2_shared.OrderType) -> 'OrderType':
        return cls(order_type)

    def to_protobuf(self) -> int:
        return self.value