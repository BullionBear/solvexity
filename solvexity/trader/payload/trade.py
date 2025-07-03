from solvexity.connector.types import Trade, Symbol, InstrumentType, OrderSide, Exchange
from pydantic import BaseModel, Field
from decimal import Decimal, ROUND_HALF_UP
from influxdb_client import Point, WritePrecision
from influxdb_client.client.flux_table import FluxRecord
from typing import Union


class TradePayload(BaseModel):
    id: int = Field(..., description="The id of the trade")
    exchange: str = Field(..., description="The exchange of the trade")
    symbol: str = Field(..., description="The symbol of the trade, e.g. BTC-USDT-SPOT")
    price: Decimal = Field(..., description="The price of the trade")
    quantity: Decimal = Field(..., description="The quantity of the trade")
    timestamp: int = Field(..., description="The time of the trade")
    side: str = Field(..., description="The side of the trade")

    @classmethod
    def from_trade(cls, trade: Trade) -> "TradePayload":
        return cls(
            id=trade.id,
            exchange=trade.exchange.value,
            symbol=f"{trade.symbol.base_currency}-{trade.symbol.quote_currency}-{trade.symbol.instrument_type.value}",
            price=trade.price,
            quantity=trade.quantity,
            timestamp=trade.timestamp,
            side=trade.side.value,
        )

    def to_trade(self) -> Trade:
        base_currency, quote_currency, instrument_type = self.symbol.split("-")
        instrument = InstrumentType(instrument_type)
        return Trade(
            id=self.id,
            exchange=Exchange(self.exchange),
            symbol=Symbol(base_currency=base_currency, quote_currency=quote_currency, instrument_type=instrument),
            price=self.price,
            quantity=self.quantity,
            timestamp=self.timestamp,
            side=OrderSide(self.side),
        )
    
    def to_point(self) -> Point:
        self.timestamp = self.timestamp * 1_000_000 # from ms to ns
        timestamp_ns = self.timestamp + self.id % 1_000_000 # add 1ns for each trade to avoid duplicates
        return Point("trades") \
            .tag("exchange", self.exchange) \
            .tag("symbol", self.symbol) \
            .field("id", self.id) \
            .field("side", self.side) \
            .field("price", self.price) \
            .field("price_str", str(self.price)) \
            .field("quantity", self.quantity) \
            .field("quantity_str", str(self.quantity)) \
            .time(timestamp_ns, write_precision=WritePrecision.NS)
    
    @classmethod
    def from_record(cls, record: FluxRecord) -> "TradePayload":
        return cls(
            id=int(record.values.get("id")),
            exchange=record.values.get("exchange"),
            symbol=record.values.get("symbol"),
            price=Decimal(record.values.get("price_str")),
            quantity=Decimal(record.values.get("quantity_str")),
            timestamp=int(record.get_time().timestamp() * 1000),
            side=record.values.get("side"),
        )
    
class InfluxTradeRequest(BaseModel):
    exchange: str
    symbol: str
    duration: str

class InfluxTradeReply(BaseModel):
    trades: list[TradePayload]

    